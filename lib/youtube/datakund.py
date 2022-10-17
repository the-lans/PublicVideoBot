from bot_studio import *
from pathlib import Path
from lib.tglogging import tgconf


class DKYouTube:
    def __init__(self):
        # self.dk = bot_studio.new()
        self.youtube = bot_studio.youtube()

    def validate_inputs(self, filename, metadata):
        if not metadata['title']:
            metadata['title'] = Path(filename).stem

    def login(self):
        with open(tgconf['cookies'], 'rt') as ft:
            cookies = json.load(ft)
        # self.dk.youtube_login_cookie(cookies=cookies)
        self.youtube.login_cookie(cookies=cookies)

    def upload(self, filename, metadata):
        self.validate_inputs(filename, metadata)
        # return self.dk.youtube_upload(
        return self.youtube.upload(
            video_path=filename,
            title=metadata['title'],
            description=metadata['description'],
            kid_type="Yes, it's made for kids",
            type='Private',
        )
