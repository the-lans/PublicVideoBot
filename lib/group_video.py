from os.path import join, isfile
from os import remove

from lib.tglogging import tgbot


class GroupVideo:
    def __init__(self, path):
        self._path = path
        self._filenames = []
        self._name = None
        self.is_each = False

    def set_name(self, name):
        self._name = name

    def get_name(self, postfix=''):
        if self._name and postfix:
            return f'{self._name} {postfix}'
        else:
            return self._name

    def add(self, filename):
        self._filenames.append(filename)

    def get_len(self):
        return len(self._filenames)

    def clear(self):
        self.set_name(None)
        for item in self._filenames:
            filename = join(self._path, item)
            if isfile(filename):
                remove(filename)
        self._filenames = []

    def is_clear(self):
        return False if self._filenames else True

    def download(self, file_id, file_name):
        file_info = tgbot.get_file(file_id)
        downloaded_file = tgbot.download_file(file_info.file_path)
        with open(join(self._path, file_name), 'wb') as fb:
            fb.write(downloaded_file)
        self.add(file_name)
