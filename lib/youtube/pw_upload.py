import os
from os.path import abspath
import shutil
from typing import Optional, Tuple, Union
from pathlib import Path
from time import sleep
from datetime import datetime, date, timedelta
import logging
import json
from playwright.async_api import async_playwright

from lib.youtube.constant import Constant
from lib.youtube.exceptions import VideoIDError
from lib.youtube.utils import get_path, wait_for_processing, setscheduletime
from lib.youtube.login import confirm_logged_in


class PWUpload:
    def __init__(
        self,
        root_profile_directory: str,
        proxy_option: str = "",
        timeout: int = 3,
        watcheveryuploadstep: bool = True,
        username: str = "",
        password: str = "",
        cook: str = "",
        ytb_cookies: str = "",
        tiktok_cookies: str = "",
        recordvideo: bool = False,
    ):
        self.timeout = timeout
        self.username = username
        self.password = password
        self.cook = cook
        self.root_profile_directory = root_profile_directory
        self.proxy_option = proxy_option
        self.watcheveryuploadstep = watcheveryuploadstep
        self.ytb_cookies = ytb_cookies
        self.tiktok_cookies = tiktok_cookies
        self.context = None
        self.page = None
        self.timeout_page = 300000
        self.recordvideo = recordvideo
        self.timeout_browser = 30000
        self._playwright = None
        self.browser = None

    async def ainit(self):
        self._playwright = await self._start_playwright()
        headless = True
        if self.watcheveryuploadstep:
            headless = False
        print('whether run in view mode', headless)
        if self.proxy_option == "":
            print('start web page without proxy')
            browserLaunchOptionDict = {
                "headless": headless,
                "timeout": self.timeout_browser,
            }
        else:
            print('start web page with proxy')
            browserLaunchOptionDict = {
                "headless": headless,
                "proxy": {
                    "server": self.proxy_option,
                },
                "timeout": self.timeout_browser,
            }

        self.browser = (
            await self._start_persistent_browser(
                "firefox", user_data_dir=self.root_profile_directory, **browserLaunchOptionDict
            )
            if self.root_profile_directory
            else await self._start_browser("firefox", **browserLaunchOptionDict)
        )

    async def adeinit(self):
        self.clear_root()
        await self.close()

    def send(self, element, text: str):
        element.clear()
        sleep(self.timeout)
        element.send_keys(text)
        sleep(self.timeout)

    async def click_next(self):
        await self.page.locator(Constant.NEXT_BUTTON).click()
        sleep(self.timeout)

    async def not_uploaded(self) -> bool:
        s = await self.page.locator(Constant.STATUS_CONTAINER).text_content()
        return s.find(Constant.UPLOADED) != -1

    async def upload(
        self,
        file: str,
        title: str = "",
        description: str = "",
        thumbnail: str = "",
        publishpolicy: int = 0,
        release_offset: str = '0-1',
        publish_date: datetime = datetime(date.today().year, date.today().month, date.today().day, 10, 15),
        tags: list = None,
        closewhen100percentupload: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """Uploads a video to YouTube.
        Returns if the video was uploaded and the video id.
        """
        if not self.root_profile_directory:
            if self.recordvideo:
                self.context = await self.browser.new_context(record_video_dir="test-results")
            else:
                self.context = await self.browser.new_context()
        else:
            self.context = self.browser

        logging.debug("Firefox is now running")
        self.page = await self.browser.new_page()
        print('============tags', tags)
        if not file:
            raise FileNotFoundError(f'Could not find file with path: "{file}"')

        if self.cook and not self.cook == '':
            print('cookies existing', self.cook)
            await self.context.clear_cookies()
            await self.context.add_cookies(json.load(open(self.cook, 'r')))
            await self.page.goto(Constant.YOUTUBE_URL, timeout=self.timeout_page)
            await self.page.reload()
        else:
            await self.page.goto(Constant.YOUTUBE_URL, timeout=self.timeout_page)
            # Interact with login form
            browser_context = await self.browser.new_context(ignore_https_errors=True)
            await browser_context.clear_cookies()
            sleep(Constant.USER_WAITING_TIME)
            storage = await browser_context.storage_state(path=self.cook)
            self.context = browser_context

        islogin = confirm_logged_in(self.page)
        print('checking login status', islogin)

        if not islogin:
            print('try to load cookie files')
            await self.context.clear_cookies()
            await self.context.add_cookies(json.load(open(self.cook, 'r')))
            print('success load cookie files')
            await self.page.goto(Constant.YOUTUBE_URL, timeout=self.timeout_page)
            print('start to check login status')
            islogin = confirm_logged_in(self.page)

        # print('start change locale to english')
        # await set_channel_language_english(self.page)
        # print('finish change locale to english')
        await self.page.goto(Constant.YOUTUBE_UPLOAD_URL, timeout=self.timeout_page)
        logging.debug("Found YouTube upload Dialog Modal")

        logging.debug(f'Trying to upload "{file}" to YouTube...')
        if os.path.exists(get_path(file)):
            self.page.locator(Constant.INPUT_FILE_VIDEO)
            await self.page.set_input_files(Constant.INPUT_FILE_VIDEO, get_path(file))
        else:
            if os.path.exists(file.encode('utf-8')):
                print('file found', file)
                self.page.locator(Constant.INPUT_FILE_VIDEO)
                await self.page.set_input_files(Constant.INPUT_FILE_VIDEO, file.encode('utf-8'))
        sleep(self.timeout)
        textbox = self.page.locator(Constant.TEXTBOX)

        # fix google account verify
        try:
            while True:
                check = self.page.locator('//*[@id="dialog-title"]')
                logging.debug(f'found to YouTube account check')
                x_path = '//*[@id="textbox"]'
                if self.page.locator(x_path):
                    logging.debug(f'fix  YouTube account check')
                    break
        except:
            sleep(1)

        logging.debug(f'Trying to set "{title}" as title...')

        sleep(self.timeout)
        if len(title) > Constant.TITLE_COUNTER:
            print(
                f"Title was not set due to exceeding the maximum allowed characters ({len(title)}/{Constant.TITLE_COUNTER})"
            )
            title = title[: Constant.TITLE_COUNTER - 1]

        print('click title field to input')
        titlecontainer = self.page.locator(Constant.TEXTBOX)
        await titlecontainer.click()
        print('clear existing title')
        await self.page.keyboard.press("Backspace")
        await self.page.keyboard.press("Control+KeyA")
        await self.page.keyboard.press("Delete")
        print('filling new title')

        await self.page.keyboard.type(title)

        logging.debug(f'Trying to set "{title}" as description...')

        if description:
            if len(description) > Constant.DESCRIPTION_COUNTER:
                print(
                    f"Description was not set due to exceeding the maximum allowed characters ({len(description)}/{Constant.DESCRIPTION_COUNTER})"
                )
                description = description[:4888]

            logging.debug(f'Trying to set "{description}" as description...')
            print('click description field to input')
            await self.page.locator(Constant.DESCRIPTION_CONTAINER).click()
            print('clear existing description')
            await self.page.keyboard.press("Backspace")
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Delete")
            print('filling new  description')
            await self.page.keyboard.type(description)

        if thumbnail:
            logging.debug(f'Trying to set "{thumbnail}" as thumbnail...')
            if os.path.exists(get_path(thumbnail)):
                await self.page.locator(Constant.INPUT_FILE_THUMBNAIL).set_input_files(get_path(thumbnail))
            else:
                if os.path.exists(thumbnail.encode('utf-8')):
                    print('thumbnail found', thumbnail)
                    await self.page.locator(Constant.INPUT_FILE_THUMBNAIL).set_input_files(thumbnail.encode('utf-8'))
            sleep(self.timeout)

        logging.debug('Trying to set video to "Not made for kids"...')

        kids_section = self.page.locator(Constant.NOT_MADE_FOR_KIDS_LABEL)
        await self.page.locator(Constant.NOT_MADE_FOR_KIDS_RADIO_LABEL).click()
        sleep(self.timeout)
        print('not made for kids done')
        if tags is None or tags == "" or len(tags) == 0:
            pass
        else:
            print('tags you give', tags)
            if type(tags) == list:
                tags = ",".join(str(tag) for tag in tags)
                tags = tags[:500]
            else:
                tags = tags
            print('overwrite prefined channel tags', tags)
            if len(tags) > Constant.TAGS_COUNTER:
                print(
                    f"Tags were not set due to exceeding the maximum allowed characters ({len(tags)}/{Constant.TAGS_COUNTER})"
                )
                tags = tags[: Constant.TAGS_COUNTER]
            print('click show more button')
            sleep(self.timeout)
            await self.page.locator(Constant.MORE_OPTIONS_CONTAINER).click()

            logging.debug(f'Trying to set "{tags}" as tags...')
            await self.page.locator(Constant.TAGS_CONTAINER).locator(Constant.TEXT_INPUT).click()
            print('clear existing tags')
            await self.page.keyboard.press("Backspace")
            await self.page.keyboard.press("Control+KeyA")
            await self.page.keyboard.press("Delete")
            print('filling new  tags')
            await self.page.keyboard.type(tags)

        # Language and captions certification
        # Recording date and location
        # Shorts sampling
        # Category
        if closewhen100percentupload:
            await wait_for_processing(self.page, process=False)

        # sometimes you have 4 tabs instead of 3
        # this handles both cases
        for _ in range(3):
            try:
                await self.click_next()
                print('done next!')
            except:
                print('error next!')

        if not int(publishpolicy) in [0, 1, 2, 3]:
            publishpolicy = 0
        if int(publishpolicy) == 0:
            logging.debug("Trying to set video visibility to private...")
            await self.page.locator(Constant.PRIVATE_RADIO_LABEL).click()
        elif int(publishpolicy) == 1:
            logging.debug("Trying to set video visibility to public...")
            await self.page.locator(Constant.PUBLIC_RADIO_LABEL).click()
        elif int(publishpolicy) == 3:
            logging.debug("Trying to set video visibility to unlisted...")
            await self.page.locator(Constant.UNLISTED_RADIO_LABEL).click()
        else:
            logging.debug("Trying to set video schedule time...{publish_date}")
            if release_offset and not release_offset == "":
                print('mode a sta')
                if not int(release_offset.split('-')[0]) == 0:
                    offset = timedelta(
                        # months=int(release_offset.split('-')[0]),
                        days=int(release_offset.split('-')[-1]),
                    )
                else:
                    offset = timedelta(days=1)
                if publish_date is None:
                    publish_date = datetime(date.today().year, date.today().month, date.today().day, 10, 15)
                else:
                    publish_date += offset

            else:
                if publish_date is None:
                    publish_date = datetime(date.today().year, date.today().month, date.today().day, 10, 15)
                    offset = timedelta(days=1)
                else:
                    publish_date = publish_date

            await setscheduletime(self.page, publish_date)

        video_id = await self.get_video_id()
        # option 1 to check final upload status
        while await self.not_uploaded():
            logging.debug("Still uploading...")
            sleep(5)

        done_button = self.page.locator(Constant.DONE_BUTTON)

        if await done_button.get_attribute("aria-disabled") == "true":
            error_message = await self.page.locator(Constant.ERROR_CONTAINER).text_content()
            return False, error_message

        await done_button.click()
        print('upload process is done')

        # Wait for the dialog to disappear
        sleep(5)
        logging.info("Upload is complete")
        return True, video_id

    async def get_video_id(self) -> Optional[str]:
        video_id = None
        try:
            video_url_container = self.page.locator(Constant.VIDEO_URL_CONTAINER)
            video_url_element = video_url_container.locator(Constant.VIDEO_URL_ELEMENT)
            video_id = await video_url_element.get_attribute(Constant.HREF)
            video_id = video_id.split("/")[-1]
        except:
            raise VideoIDError("Could not get video ID")
        return video_id

    @staticmethod
    async def _start_playwright():
        return await async_playwright().start()

    async def _start_browser(self, browser: str, **kwargs):
        if browser == "chromium":
            return await self._playwright.chromium.launch(**kwargs)
        if browser == "firefox":
            return await self._playwright.firefox.launch(**kwargs)
        if browser == "webkit":
            return await self._playwright.webkit.launch(**kwargs)
        raise RuntimeError("You have to select either 'chromium', 'firefox', or 'webkit' as browser.")

    async def _start_persistent_browser(self, browser: str, user_data_dir: Optional[Union[str, Path]], **kwargs):
        if browser == "chromium":
            return await self._playwright.chromium.launch_persistent_context(user_data_dir, **kwargs)
        if browser == "firefox":
            return await self._playwright.firefox.launch_persistent_context(user_data_dir, **kwargs)
        if browser == "webkit":
            return await self._playwright.webkit.launch_persistent_context(user_data_dir, **kwargs)
        raise RuntimeError("You have to select either 'chromium', 'firefox' or 'webkit' as browser.")

    async def close(self):
        await self.browser.close()
        await self._playwright.stop()

    def clear_root(self):
        shutil.rmtree(self.root_profile_directory, ignore_errors=True)

    async def multiple_upload(self, out_names, metadata, is_init=True, is_deinit=True):
        if is_init:
            await self.ainit()
        ids = []
        for ind in range(len(out_names)):
            was_uploaded, video_id = await self.upload(
                abspath(out_names[ind]),
                title=metadata[ind]['title'],
                description=metadata[ind]['description'],
                tags=metadata[ind]['tags'],
                closewhen100percentupload=True,
                publishpolicy=metadata[ind]['policy'],
            )
            if was_uploaded:
                ids.append(video_id)
        if is_deinit:
            await self.adeinit()
        return ids
