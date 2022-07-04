import os
from pathlib import Path

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
from gtts import gTTS
import pdfplumber

from config import TOKEN

MEDIA_PATH = 'media'
PDF_PATH = 'pdf'

if not Path(MEDIA_PATH).is_dir():
    Path(MEDIA_PATH).mkdir(parents=True, exist_ok=True)
if not Path(PDF_PATH).is_dir():
    Path(PDF_PATH).mkdir(parents=True, exist_ok=True)


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Form(StatesGroup):
    waiting_file = State()
    waiting_lang = State()


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply('Привет! Отправь мне pdf файл и язык текста. В ответ получишь текст в формате mp3.')
    await Form.waiting_file.set()


@dp.message_handler(state=Form.waiting_file, content_types=["document"])
async def add_pdf_file(message: types.Message, state: FSMContext):
    if message.document.mime_type != 'application/pdf':
        await message.answer('Пожалуйста, загрузите pdf файл')
        return
    src = os.path.join(PDF_PATH, f'{message.document.file_name}')
    await state.update_data(pdf_file_name=src)
    await message.document.download(destination_file=src)
    await Form.next()
    await message.answer('Введите язык текста (например, ru или en, где ru - русский, en - английский)')


@dp.message_handler(state=Form.waiting_lang)
async def change_language(message: types.Message, state: FSMContext):
    if message.text.lower() not in ['ru', 'en', 'fr']:
        await message.answer('Пожалуйста, введите язык текста')
        return
    await state.update_data(lang=message.text.lower())
    data = await state.get_data()
    with pdfplumber.open(path_or_fp=data['pdf_file_name']) as pdf:
        await message.answer('Пожалуйста, подождите. Идет конвертирование...')
        pages = [page.extract_text() for page in pdf.pages]
        text = ''.join(pages).replace('\n', ' ')
        audio = gTTS(text=text, lang=data['lang'])
        file_name = Path(data['pdf_file_name']).stem
        file_path = os.path.join(MEDIA_PATH, f'{file_name}.mp3')
        audio.save(file_path)
        if not Path(file_path).is_file():
            await bot.send_message(message.chat.id, 'Файл не найден')
            return
        audio_file = open(file_path, 'rb')
        await bot.send_audio(message.chat.id, audio_file)
        await message.answer('Готово!')
        audio_file.close()
    await message.answer('Жду файл в формате pdf')
    await Form.waiting_file.set()


if __name__ == '__main__':
    executor.start_polling(dp)
