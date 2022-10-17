from os.path import join
import time
import datetime
import numpy as np
import cv2
import shutil
from math import isclose
from scipy.ndimage import gaussian_filter
from moviepy.editor import VideoFileClip, CompositeVideoClip, concatenate_videoclips

from lib.tglogging import tgconf
from lib.group_video import GroupVideo


# Фильтр Гаусса
def blur(image, sigma=12):
    """ Returns a blurred (radius=2 pixels) version of the image """
    flt = np.zeros(image.shape)
    flt[:, :, 0] = gaussian_filter(image[:, :, 0].astype(float), sigma=sigma)
    flt[:, :, 1] = gaussian_filter(image[:, :, 1].astype(float), sigma=sigma)
    flt[:, :, 2] = gaussian_filter(image[:, :, 2].astype(float), sigma=sigma)
    return flt


# Изменение размера картинки для размытия
def blurred(holst, clip):
    return clip.resize(holst).fl_image(blur)


# Определение размеров холста
def get_holst(size, koef=16 / 9):
    clip_koef = size[0] / size[1]
    if clip_koef < koef:
        return (round(koef * size[1]), size[1])
    else:
        return (size[0], round(size[0] / koef))


# Возвращает ось, по которой "прокручивается" картинка
def get_axis_rests(holst, clip, clip_size=None):
    if clip_size is None:
        clip_size = clip.size
    img_koef = clip_size[0] / clip_size[1]
    holst_koef = holst[0] / holst[1]
    return 'x' if img_koef >= holst_koef else 'y'


# Изменение размера картинки под холст
def clip_resize(holst, clip, koef=1.0, wh=True, clip_size=None):
    w = int(koef * holst[0])
    h = int(koef * holst[1])
    axis = get_axis_rests(holst, clip, clip_size=clip_size)
    clip_sz = clip
    if clip_size is None:
        clip_size = clip.size
    if wh:
        if axis == 'x' and clip_size[0] != w:
            clip_sz = clip.resize(width=w)
            print(f'Resize width: {clip_size[0]} -> {w}')
            clip_sz = clip_sz.set_pos(('center', 'center'))
        elif axis == 'y' and clip_size[1] != h:
            clip_sz = clip.resize(height=h)
            print(f'Resize height: {clip_size[1]} -> {h}')
            clip_sz = clip_sz.set_pos(('center', 'center'))
    else:
        if axis == 'y' and clip_size[0] != w:
            clip_sz = clip.resize(width=w)
            print(f'Resize width: {clip_size[0]} -> {w}')
            clip_sz = clip_sz.set_pos(('center', 'center'))
        elif axis == 'x' and clip_size[1] != h:
            clip_sz = clip.resize(height=h)
            print(f'Resize height: {clip_size[1]} -> {h}')
            clip_sz = clip_sz.set_pos(('center', 'center'))
    return clip_sz


# Центрирование видео
def clip_center(holst, clip, koef=1.0, wh=True, clip_size=None):
    w = int(koef * holst[0])
    h = int(koef * holst[1])
    axis = get_axis_rests(holst, clip, clip_size=clip_size)
    clip_sz = clip
    if clip_size is None:
        clip_size = clip.size
    if wh:
        if (axis == 'x' and clip_size[0] != w) or (axis == 'y' and clip_size[1] != h):
            clip_sz = clip_sz.set_pos(('center', 'center'))
    else:
        if (axis == 'y' and clip_size[0] != w) or (axis == 'x' and clip_size[1] != h):
            clip_sz = clip_sz.set_pos(('center', 'center'))
    return clip_sz


# Возврат коэффициента
def get_clip_koef(size):
    return size[0] / size[1]


# Разрешение видео
def get_cv_size(filename):
    vid = cv2.VideoCapture(filename)
    return int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))


# Окончательный рендер клипа
def video_render(holst, render_clips, out_name, isblur=True, isresize=True):
    array_clips = []
    for clip in render_clips:
        clip_size = get_cv_size(clip.reader.filename)
        if isresize:
            clip = clip_resize(holst, clip, clip_size=clip_size)
        else:
            clip = clip.resize(clip_size)
        if isblur and not isclose(get_clip_koef(holst), get_clip_koef(clip_size), abs_tol=0.01):
            clip = CompositeVideoClip([blurred(holst, clip), clip])
        array_clips.append(clip)
    final = concatenate_videoclips(array_clips, method='compose')
    final.write_videofile(out_name, fps=final.fps, codec='libx264')
    final.close()


# Наименование модели
def get_name_model(prefix='out'):
    st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d_%H%M%S')
    return f'{prefix}_{st}'


# Видео-процессинг
def video_processing(inp: GroupVideo, out_path: str):
    render_clips1 = []
    render_clips2 = []
    size_max1 = (0, 0)
    size_max2 = (0, 0)
    for name in inp._filenames:
        clip = VideoFileClip(join(inp._path, name))
        clip_size = get_cv_size(join(inp._path, name))
        if clip.duration >= tgconf['duration_min']:
            if get_clip_koef(clip_size) > 1.0:
                size_max1 = (max(size_max1[0], clip_size[0]), max(size_max1[1], clip_size[1]))
                render_clips1.append(clip)
            else:
                size_max2 = (max(size_max2[0], clip_size[0]), max(size_max2[1], clip_size[1]))
                render_clips2.append(clip)

    result = []
    basename = get_name_model('out')
    if render_clips1:
        out_name = join(out_path, f"{basename}_1.avi")
        video_render(
            get_holst(size_max1, 16 / 9), render_clips1, out_name, isblur=tgconf['blur'], isresize=tgconf['resize']
        )
        result.append(out_name)
    if render_clips2:
        out_name = join(out_path, f"{basename}_2.avi")
        video_render(
            get_holst(size_max2, 9 / 16), render_clips2, out_name, isblur=tgconf['blur'], isresize=tgconf['resize']
        )
        result.append(out_name)
    return result


# Видео-процессинг каждого видео
def video_processing_each(inp: GroupVideo, out_path: str):
    result = []
    for name in inp._filenames:
        out_name = join(out_path, name)
        inp_name = join(inp._path, name)
        clip = VideoFileClip(inp_name)
        clip_size = get_cv_size(inp_name)
        if list(clip_size) == list(clip.size):
            clip.close()
            shutil.move(inp_name, out_name)
        else:
            final = clip.resize(clip_size)
            final.write_videofile(out_name, fps=final.fps, codec='libx264')
            clip.close()
            final.close()
        result.append(out_name)
    return result
