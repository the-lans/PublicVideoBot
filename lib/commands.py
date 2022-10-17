from os.path import isfile, abspath, join
from os import listdir
import shutil
from datetime import datetime
from pathlib import Path
import asyncio

from lib.tglogging import tgconf, tgbot
from lib.video_processing import video_processing, video_processing_each
from lib.youtube.upload import get_authenticated_service, initialize_upload
from lib.youtube.selenium import YouTubeUploader
from lib.youtube.datakund import DKYouTube
from lib.youtube.pw_upload import PWUpload
from lib.func import remove_files


def command_upload(chat_id, out_names, main_group_video):
    # Metadata
    tgbot.send_message(chat_id, 'Загрузка на YouTube...')
    current_datetime = datetime.now()
    postfix = ['(горизонтально)', '(вертикально)']
    metadata = []
    for ind in range(len(out_names)):
        title = main_group_video.get_name(
            postfix=postfix[ind] if not main_group_video.is_each and len(out_names) > 1 else ''
        )
        if not title:
            title = Path(out_names[ind]).stem
        metadata.append(
            {
                'title': title,
                'description': tgconf['youtube_description'],
                'tags': f"{tgconf['youtube_tags']},{current_datetime.year}",
                'category': tgconf['youtube_category'],
                'policy': tgconf['youtube_policy'],
            }
        )

    # Upload
    ids = []
    if tgconf['uploader'] == 'selenium':
        for ind in range(len(out_names)):
            uploader = YouTubeUploader(out_names[ind], metadata[ind])
            was_uploaded, video_id = uploader.upload()
            if was_uploaded:
                ids.append(video_id)
                send_ref_youtube(chat_id, video_id)

    elif tgconf['uploader'] == 'bot':
        youtube = DKYouTube()
        youtube.login()
        for ind in range(len(out_names)):
            response = youtube.upload(abspath(out_names[ind]), metadata[ind])
            video_id = response['body']['VideoLink']
            ids.append(video_id)
            send_ref_youtube(chat_id, video_id)

    elif tgconf['uploader'] == 'api':
        youtube = get_authenticated_service('youtube', 'v3')
        for ind in range(len(out_names)):
            response = initialize_upload(
                youtube,
                file=out_names[ind],
                title=metadata[ind]['title'],
                description=metadata[ind]['description'],
                keywords=metadata[ind]['tags'],
                category=metadata[ind]['category'],
            )
            video_id = response['id']
            ids.append(video_id)
            send_ref_youtube(chat_id, video_id)

    elif tgconf['uploader'] == 'playwright':

        async def upload_files():
            await youtube.ainit()
            try:
                for ind in range(len(out_names)):
                    video_ids = await youtube.multiple_upload(
                        [out_names[ind]], [metadata[ind]], is_init=False, is_deinit=False
                    )
                    ids.append(video_ids[0])
                    send_ref_youtube(chat_id, video_ids[0])
            except Exception as e:
                print(e)
            finally:
                await youtube.adeinit()

        youtube = PWUpload(
            abspath(tgconf['profile']),
            # proxy_option='socks5://127.0.0.1:1080',
            watcheveryuploadstep=True,
            # if you want to silent background running, set watcheveryuploadstep false
            cook=tgconf['cookies'],
            username=tgconf['youtube_login'],
            password=tgconf['youtube_pass'],
            recordvideo=True,
            # for test purpose we need to check the video step by step
        )
        asyncio.run(upload_files())


def command_process(func):
    def _wrapper(chat_id, main_group_video):
        # Init
        if main_group_video.is_clear():
            tgbot.send_message(chat_id, 'Нечего обрабатывать')
            return

        # Process
        tgbot.send_message(chat_id, 'Процессинг видео...')
        out_names = func(chat_id, main_group_video)

        # Upload
        command_upload(chat_id, out_names, main_group_video)

        # Destructor
        main_group_video.clear()
        # remove_files(out_names)

    return _wrapper


def send_ref_youtube(chat_id, video_id):
    tgbot.send_message(chat_id, f"Ссылка: https://youtu.be/{video_id}")


@command_process
def command_video_process(chat_id, main_group_video):
    return video_processing(main_group_video, tgconf['processing_path'])


@command_process
def command_video_process_each(chat_id, main_group_video):
    return video_processing_each(main_group_video, tgconf['processing_path'])


def command_begin(chat_id, main_group_video):
    main_group_video.clear()
    out_names = listdir(tgconf['processing_path'])
    remove_files(out_names, tgconf['processing_path'])
    tgbot.send_message(chat_id, 'Начнём. Введите название группы и загрузите видео.')


def command_collect(chat_id, main_group_video):
    filenames = listdir(tgconf['load_path'])
    for name in filenames:
        filename = join(tgconf['load_path'], name)
        if isfile(filename):
            shutil.move(filename, join(tgconf['received_path'], name))
            main_group_video.add(name)
            print(name)
    print(f'{len(filenames)} files have been added')
    tgbot.send_message(chat_id, f'Было добавлено файлов: {len(filenames)}\nВсего файлов: {main_group_video.get_len()}')


def command_text(message, main_group_video):
    main_group_video.set_name(message.text.strip())
