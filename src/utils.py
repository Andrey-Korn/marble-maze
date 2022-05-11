import cv2 as cv
import numpy as np
import yaml

# Maps example videos to paths
vid_prefix = "../videos"
video_path_map = {
    # Metal ball
    "metal_1":      f'{vid_prefix}/2022-01-23 12-25-15.mp4',
    "metal_2":      f'{vid_prefix}/2022-01-23 12-25-59.mp4',
    "metal_3":      f'{vid_prefix}/2022-01-23 12-26-33.mp4',
    "metal_4":      f'{vid_prefix}/2022-01-23 12-27-05.mp4',

    # Colored ball - orignal
    "blue":         f'{vid_prefix}/2022-03-02 09-51-06.mp4',
    "green":        f'{vid_prefix}/2022-03-02 09-50-40.mp4',
    "red":          f'{vid_prefix}/2022-03-02 09-50-12.mp4',

    # Colored ball - higher brightness
    "blue_bright":  f'{vid_prefix}/2022-03-03 14-06-09.mp4',
    "green_bright": f'{vid_prefix}/2022-03-03 14-05-22.mp4',
    "red_bright":   f'{vid_prefix}/2022-03-03 14-04-44.mp4',
}

# Maps color name strings to tuples representing BGR (Blue Green Red) color values
color_map = {
    "white":        (255,   255,    255 ),
    "black":        (0,     0,      0   ),
    "blue":         (255,   0,      0   ),
    "green":        (0,     255,    0   ),
    "red":          (0,     0,      255 ),
    "yellow":       (0,     255,    255 ),
    "cyan":         (255,   255,    0   ),
    "orange":       (0,     128,    255 ),
    "brightorange": (0,     192,    255 ),
    "magenta":      (255,   0,      255 )
}

# config file map
config_prefix = 'confs'
config_files = {
    "camera_1080": f'{config_prefix}/camera_config_1080.yaml',
    "camera_720": f'{config_prefix}/camera_config_720.yaml',
    "serial": f'{config_prefix}/serial.yaml'
}


def read_yaml(conf):
    settings = None
    with open(conf, 'r') as file:
        settings = yaml.safe_load(file)
    return settings

def crop_frame(frame, x_frame, y_frame):
    return frame[x_frame[0]:x_frame[1], y_frame[0]:y_frame[1], :]

# cv functions
def draw_text(img: np.ndarray, text:str, position: tuple, BGR_color: tuple) -> None:
    """ Draws text of color BGR_color to img at position """

    new_img = cv.putText(img, text, position, cv.FONT_HERSHEY_SIMPLEX, 2, BGR_color, 3)
    img = new_img


def draw_circles(img: np.ndarray, circles: list, num: int = -1, BGR_color: tuple = (0, 0, 255)) -> None:
    """ Draws output from cv.HoughCircles onto img """

    circle_rad = 25

    if num == -1:
        num = len(circles)

    for c in circles[:num]:
        cv.circle(img, (c[0],c[1]), circle_rad, BGR_color, 3)   # Draw circle
        cv.circle(img, (c[0],c[1]), 2, BGR_color, 3)   # Draw dot at circle's center

    return
