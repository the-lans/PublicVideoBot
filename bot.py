import shutil
from telebot import types
from time import sleep
from os import listdir

from lib.tglogging import newdir, tgconf, tgbot
from lib.group_video import GroupVideo
from lib.commands import (
    command_video_process,
    command_video_process_each,
    command_begin,
    command_collect,
    command_text,
    command_upload,
)


# Команда start
@tgbot.message_handler(commands=['start'])
def handle_start(message, res=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = [types.KeyboardButton(name) for name in ['Начать', 'Выполнить', 'Собрать', 'Загрузить каждый']]
    markup.add(items[0])
    markup.add(items[1], items[2], items[3])
    tgbot.send_message(message.chat.id, 'Начнём загрузку видео', reply_markup=markup)


# Команда upload
@tgbot.message_handler(commands=['upload'])
def handle_upload(message, res=False):
    chat_id = message.chat.id
    out_names = listdir(tgconf['processing_path'])
    command_upload(chat_id, out_names, main_group_video)


# Получение сообщений от юзера
@tgbot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if message.text.strip().lower() == 'начать':
        command_begin(chat_id, main_group_video)
    elif message.text.strip().lower() == 'собрать':
        command_collect(chat_id, main_group_video)
    elif message.text.strip().lower() == 'выполнить':
        main_group_video.is_each = False
        command_video_process(chat_id, main_group_video)
    elif message.text.strip().lower() == 'загрузить каждый':
        main_group_video.is_each = True
        command_video_process_each(chat_id, main_group_video)
    else:
        command_text(message, main_group_video)


# Файл с видео
@tgbot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id
    for ind in range(3):
        try:
            ext = message.video.mime_type.split('/')[-1]
            filename = f'{message.video.file_unique_id}.{ext}'
            main_group_video.download(message.video.file_id, filename)
            print(f'Downloaded {ind}: {filename}')
            tgbot.send_message(chat_id, f'Пожалуй, я сохраню это: {filename}')
            break
        except Exception as e:
            print(e)
            tgbot.send_message(chat_id, e)
            sleep(2)


# Запускаем бота
newdir(tgconf['log_dir'])
shutil.rmtree(tgconf['profile'], ignore_errors=True)
main_group_video = GroupVideo(tgconf['received_path'])
tgbot.infinity_polling()
