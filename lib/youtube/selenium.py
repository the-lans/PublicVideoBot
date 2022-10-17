from typing import Optional
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from os.path import abspath
from pathlib import Path
import logging
import platform

from lib.youtube.constant import Constant
from lib.tglogging import tgconf
from lib.func import read_cookies


class YouTubeUploader:
    """A class for uploading videos on YouTube via Selenium using metadata JSON file
    to extract its title, description etc"""

    def __init__(self, video_path: str, metadata: dict, thumbnail_path: Optional[str] = None) -> None:
        self.video_path = video_path
        self.thumbnail_path = thumbnail_path
        self.metadata_dict = metadata
        # current_working_dir = abspath(tgconf['data_path'])
        # self.browser = Firefox(current_working_dir, current_working_dir, geckodriver_path=tgconf['geckodriver_path'])
        options = Options()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64)')
        self.browser = webdriver.Firefox(executable_path=abspath(tgconf['geckodriver_path']), options=options)
        self.is_mac = not any(os_name in platform.platform() for os_name in ["Windows", "Linux"])
        self.__validate_inputs()

    def __validate_inputs(self):
        if not self.metadata_dict['title']:
            logging.warning("The video title was not found in a metadata file")
            self.metadata_dict['title'] = Path(self.video_path).stem
            logging.warning("The video title was set to {}".format(Path(self.video_path).stem))
        if not self.metadata_dict['description']:
            logging.warning("The video description was not found in a metadata file")

    def upload(self):
        try:
            self.__login()
            return self.__upload()
        except Exception as e:
            print(e)
            self.__quit()
            raise

    def load_cookies(self, filter_domain):
        for cookie in read_cookies(tgconf['cookies']):
            if cookie['domain'] == filter_domain:
                self.browser.add_cookie(cookie)

    def __login(self):
        self.browser.get(Constant.YOUTUBE_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        self.load_cookies(Constant.YOUTUBE_DOMAIN)
        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)
        time.sleep(Constant.USER_WAITING_TIME)

        try:
            login_field = self.browser.find_element(By.NAME, Constant.INPUT_EMAIL)
        except:
            logging.info('Google authentication successful!')
        else:
            self.__write_in_field(login_field, tgconf['youtube_login'], select_all=False)
            self.browser.find_element(By.ID, Constant.BUTTON_EMAIL_NEXT).click()
            time.sleep(Constant.USER_WAITING_TIME)

            login_field = self.browser.find_element(By.NAME, Constant.INPUT_PASS)
            self.__write_in_field(login_field, tgconf['youtube_pass'], select_all=False)
            self.browser.find_element(By.ID, Constant.BUTTON_PASS_NEXT).click()
            time.sleep(Constant.USER_WAITING_TIME)
            logging.info('Google authentication successful!')

    def __write_in_field(self, field, string, select_all=False):
        field.click()
        time.sleep(Constant.USER_WAITING_TIME)
        if select_all:
            field.send_keys((Keys.COMMAND if self.is_mac else Keys.CONTROL) + 'a')
            time.sleep(Constant.USER_WAITING_TIME)
        field.send_keys(string)

    def __upload(self) -> (bool, Optional[str]):
        self.browser.get(Constant.YOUTUBE_UPLOAD_URL)
        time.sleep(Constant.USER_WAITING_TIME)
        absolute_video_path = abspath(self.video_path)
        self.browser.find_element(By.XPATH, Constant.INPUT_FILE_VIDEO).send_keys(absolute_video_path)
        logging.debug('Attached video {}'.format(self.video_path))

        if self.thumbnail_path is not None:
            absolute_thumbnail_path = abspath(self.thumbnail_path)
            self.browser.find_element(By.XPATH, Constant.INPUT_FILE_THUMBNAIL).send_keys(absolute_thumbnail_path)
            change_display = "document.getElementById('file-loader').style = 'display: block! important'"
            self.browser.execute_script(change_display)
            logging.debug('Attached thumbnail {}'.format(self.thumbnail_path))

        title_field = self.browser.find_element(By.ID, Constant.TEXTBOX)
        self.__write_in_field(title_field, self.metadata_dict['title'], select_all=True)
        logging.debug('The video title was set to \"{}\"'.format(self.metadata_dict['title']))

        video_description = self.metadata_dict['description']
        video_description = video_description.replace("\n", Keys.ENTER)
        if video_description:
            description_field = self.browser.find_elements(By.ID, Constant.TEXTBOX)[1]
            self.__write_in_field(description_field, video_description, select_all=True)
            logging.debug('Description filled.')

        kids_section = self.browser.find_element(By.NAME, Constant.NOT_MADE_FOR_KIDS_LABEL)
        kids_section.find_element(By.ID, Constant.RADIO_LABEL).click()
        logging.debug('Selected \"{}\"'.format(Constant.NOT_MADE_FOR_KIDS_LABEL))

        # Advanced options
        self.browser.find_element(By.XPATH, Constant.MORE_BUTTON).click()
        logging.debug('Clicked MORE OPTIONS')

        tags_container = self.browser.find_element(By.XPATH, Constant.TAGS_INPUT_CONTAINER)
        tags_field = tags_container.find_element(By.ID, Constant.TAGS_INPUT)
        self.__write_in_field(tags_field, ','.join(self.metadata_dict['tags']))
        logging.debug('The tags were set to \"{}\"'.format(self.metadata_dict['tags']))

        self.browser.find_element(By.ID, Constant.NEXT_BUTTON).click()
        logging.debug('Clicked {} one'.format(Constant.NEXT_BUTTON))

        self.browser.find_element(By.ID, Constant.NEXT_BUTTON).click()
        logging.debug('Clicked {} two'.format(Constant.NEXT_BUTTON))

        self.browser.find_element(By.ID, Constant.NEXT_BUTTON).click()
        logging.debug('Clicked {} three'.format(Constant.NEXT_BUTTON))
        public_main_button = self.browser.find_element(By.NAME, Constant.PUBLIC_BUTTON)
        public_main_button.find_element(By.ID, Constant.RADIO_LABEL).click()
        logging.debug('Made the video {}'.format(Constant.PUBLIC_BUTTON))

        video_id = self.__get_video_id()
        status_container = self.browser.find_element(By.XPATH, Constant.STATUS_CONTAINER)
        while True:
            in_process = status_container.text.find(Constant.UPLOADED) != -1
            if in_process:
                time.sleep(Constant.USER_WAITING_TIME)
            else:
                break

        done_button = self.browser.find_element(By.ID, Constant.DONE_BUTTON)

        # Catch such error as
        # "File is a duplicate of a video you have already uploaded"
        if done_button.get_attribute('aria-disabled') == 'true':
            error_message = self.browser.find_element(By.XPATH, Constant.ERROR_CONTAINER).text
            logging.error(error_message)
            return False, None

        done_button.click()
        logging.debug("Published the video with video_id = {}".format(video_id))
        time.sleep(Constant.USER_WAITING_TIME)
        self.browser.get(Constant.YOUTUBE_URL)
        self.__quit()
        return True, video_id

    def __get_video_id(self) -> Optional[str]:
        video_id = None
        try:
            video_url_container = self.browser.find_element(By.XPATH, Constant.VIDEO_URL_CONTAINER)
            video_url_element = video_url_container.find_element(By.XPATH, Constant.VIDEO_URL_ELEMENT)
            video_id = video_url_element.get_attribute(Constant.HREF).split('/')[-1]
        except:
            logging.warning(Constant.VIDEO_NOT_FOUND_ERROR)
        return video_id

    def __quit(self):
        self.browser.quit()
