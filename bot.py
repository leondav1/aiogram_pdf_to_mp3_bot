import os
from pathlib import Path

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from gtts import gTTS
import pdfplumber

from config import token

MEDIA_PATH = 'media'

if not Path(MEDIA_PATH).is_dir():
    Path(MEDIA_PATH).mkdir(parents=True, exist_ok=True)

bot = Bot(token=token)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply('Привет! Отправь мне pdf файл и язык текста. В ответ получишь текст в формате mp3.')


@dp.message_handler(content_types=["document"])
async def sticker_file_id(message: types.Message):
    # await message.answer(f"{message.document.file_name}")
    with pdfplumber.open(path_or_fp=message.document.file_name) as pdf:
        await message.answer('Пожалуйста, подождите. Идет конвертирование...')
        pages = [page.extract_text() for page in pdf.pages]
        text = ''.join(pages).replace('\n', ' ')
        audio = gTTS(text=text, lang='en')
        file_name = Path(message.document.file_name).stem
        file_path = os.path.join(MEDIA_PATH, f'{file_name}.mp3')
        audio.save(file_path)
        if not Path(file_path).is_file():
            await bot.send_message(message.chat.id, 'Файл не найден')
            return
        audio_file = open(file_path, 'rb')
        await bot.send_audio(message.chat.id, audio_file)
        await message.answer('Готово!')
        audio_file.close()


if __name__ == '__main__':
    executor.start_polling(dp)
