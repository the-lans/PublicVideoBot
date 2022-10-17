class Constant:
    """A class for storing constants for YoutubeUploader class"""

    YOUTUBE_URL = 'https://www.youtube.com'
    YOUTUBE_DOMAIN = '.youtube.com'
    YOUTUBE_STUDIO_URL = 'https://studio.youtube.com'
    YOUTUBE_UPLOAD_URL = 'https://www.youtube.com/upload'
    USER_WAITING_TIME = 1
    TEXTBOX = '#title-textarea'
    TEXT_INPUT = '#text-input'
    RADIO_LABEL = 'radioLabel'
    NOT_MADE_FOR_KIDS_LABEL = 'VIDEO_MADE_FOR_KIDS_NOT_MFK'
    MORE_BUTTON = (
        '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/'
        'ytcp-video-metadata-editor/div/div/ytcp-button/div'
    )
    TAGS_INPUT = 'text-input'
    VIDEO_URL_ELEMENT = "//a[@class='style-scope ytcp-video-info']"
    HREF = 'href'
    UPLOADED = 'Uploading'
    VIDEO_NOT_FOUND_ERROR = 'Could not find video_id'
    DONE_BUTTON = "//*[@id='done-button']"
    NEXT_BUTTON = "//*[@id='next-button']"
    INPUT_FILE_VIDEO = "//input[@type='file']"
    INPUT_FILE_THUMBNAIL = "//input[@id='file-loader']"
    INPUT_EMAIL = "identifier"
    BUTTON_EMAIL_NEXT = "identifierNext"
    INPUT_PASS = "password"
    BUTTON_PASS_NEXT = "passwordNext"

    # CONTAINERS
    CONFIRM_CONTAINER = '#confirmation-dialog'
    TAGS_CONTAINER = '//*[@id="tags-container"]'
    ERROR_CONTAINER = '//*[@id="error-message"]'
    STATUS_CONTAINER = (
        '//html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/'
        'div/div[1]/ytcp-video-upload-progress/span'
    )
    VIDEO_URL_CONTAINER = "//span[@class='video-url-fadeable style-scope ytcp-video-info']"
    DESCRIPTION_CONTAINER = "//*[@id='description-container']"
    MORE_OPTIONS_CONTAINER = "#toggle-button > div:nth-child(2)"
    TAGS_INPUT_CONTAINER = (
        '/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/'
        'ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-advanced/div[3]/'
        'ytcp-form-input-container/div[1]/div[2]/ytcp-free-text-chip-bar/ytcp-chip-bar/div'
    )
    TIME_BETWEEN_POSTS = 3600

    # COUNTERS
    TAGS_COUNTER = 500
    TITLE_COUNTER = 100
    DESCRIPTION_COUNTER = 5000

    # OTHER
    NOT_MADE_FOR_KIDS_RADIO_LABEL = (
        "tp-yt-paper-radio-button.ytkc-made-for-kids-select:nth-child(2) > div:nth-child(2) > ytcp-ve:nth-child(1)"
    )
    PUBLIC_RADIO_LABEL = '//tp-yt-paper-radio-button[@name="PUBLIC"]'
    PRIVATE_RADIO_LABEL = '//tp-yt-paper-radio-button[@name="PRIVATE"]'
    UNLISTED_RADIO_LABEL = '//tp-yt-paper-radio-button[@name="UNLISTED"]'
    PUBLIC_BUTTON = "PUBLIC"
    PRIVATE_BUTTON = "PRIVATE"
    UNLISTED_BUTTON = "UNLISTED"
