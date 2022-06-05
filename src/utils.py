import cv2 as cv
import numpy as np
from numpy.lib import utils
import yaml
import argparse

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
    "serial": f'{config_prefix}/serial.yaml',
    "easy": f'{config_prefix}/maze_easy.yaml',
    "med": f'{config_prefix}/maze_med.yaml',
    "hard": f'{config_prefix}/maze_hard.yaml'
}

path_prefix = 'paths'
path_files = {
    'hard': f'{path_prefix}/hard.json',
    'hard_transform': f'{path_prefix}/hard_transform.json',
    'line': f'{path_prefix}/line.json',
    'rectangle': f'{path_prefix}/rectangle.json',
    'small_rectangle': f'{path_prefix}/small_rectangle.json'
}

def setup_arg_parser(desc, maze_req=True):
    parser = argparse.ArgumentParser(description=desc)
    # get maze config
    parser.add_argument('-m', '--maze', type=str, nargs=1, 
                        help='specify maze config file')

    # get camera config
    parser.add_argument('-c', '--camera', type=str, nargs=1,
                        help='specify camera YAML config file')

    # get path file
    parser.add_argument('-p', '--path', type=str, nargs=1,
                        help='specify path JSON file')

    args = parser.parse_args()
    if args.camera == None:
        args.camera = config_files['camera_720']

    if args.maze == None:
        args.maze = config_files['hard']

    if args.path == None:
        # args.path = path_files['line']
        # args.path = path_files['rectangle']
        args.path = path_files['small_rectangle']
        # args.path = path_files['hard']
        # args.path = path_files['hard_transform']
    else:
        args.path = args.path[0]

    print(args)
    return args

# read in yaml config 
def read_yaml(conf):
    settings = None
    with open(conf, 'r') as file:
        settings = yaml.safe_load(file)
    return settings

# crop frame based on camera config file
def crop_frame(frame, height, width):
    return frame[height[0]:height[1], width[0]:width[1], :]

# error calculation: (delta_x, delta_y)
def ball_error(ball_pos, target) -> tuple:
    return (target[0] - ball_pos[0], target[1] - ball_pos[1])

def at_target(error, range):
    return (abs(error[0]) < range and abs(error[1]) < range)

def normalize_magnitudes(raw):
    x, y = raw[0], raw[1]
    # print(f'raw: x: {x}, y: {y}')
    # if x == 0 or y == 0:
        # return raw 
    # alpha = np.arctan(float(y)/x)
    # print(f'aplha: {alpha}')
    # y = np.round(y * np.sin(alpha), 2)
    # x = np.round(x * np.cos(alpha), 2)
    # print(f'dif: x: {x}, y: {y}')

    s = abs(x) + abs(y)
    # print(s)
    if  s > 1:
        x = np.round(float(x) / (s), 2)
        y = np.round(float(y) / (s), 2)
    # print([x, y])
    return [x, y]

# cv functions
def draw_text(img: np.ndarray, text:str, position: tuple, BGR_color: tuple, font_size=1.5) -> None:
    """ Draws text of color BGR_color to img at position """
    cv.putText(img, text, position, cv.FONT_HERSHEY_SIMPLEX, font_size, BGR_color, 3)

def annotate_point(img: np.ndarray, text:str, position: tuple, BGR_color:tuple) -> None:
    draw_text(img, text, (position[0] + 25 ,position[1] + 25), BGR_color, font_size=1)

def draw_line(img: np.ndarray, start, end, BGR_color: tuple=color_map['orange'], thickness=2):
    cv.line(img, start, end, BGR_color, thickness)

def draw_magnitude(img: np.ndarray, start, tilt, scalar:int, BGR_color: tuple=color_map['orange'], thickness=2):
    start = (start[0], start[1])
    # print(tilt)
    end = (int(start[0] + (scalar * tilt[0])), int(start[1] + (-scalar * tilt[1])))
    # print(start)
    # print(end)
    draw_line(img, start, end, BGR_color, thickness)

def draw_circles(img: np.ndarray, circles: list, num: int = -1, BGR_color: tuple = (0, 0, 255), annotate=False) -> None:
    """ Draws output from cv.HoughCircles onto img """

    if num == -1:
        num = len(circles)

    i = 1
    for c in circles[:num]:
        cv.circle(img, (c[0],c[1]), c[2], BGR_color, 3)   # Draw circle
        cv.circle(img, (c[0],c[1]), 2, BGR_color, 3)   # Draw dot at circle's center
        if annotate:
            annotate_point(img, f'{i}', (c[0], c[1]), BGR_color)
            i += 1
    return

def draw_corners(img: np.ndarray, pts, BGR_color:tuple = color_map['blue']):
    for p in pts:
        cv.circle(img, (p[0].astype(int), p[1].astype(int)), 7, BGR_color, 2)

def display_performance(frame, location, spacing, start, end, frame_time, text_size):
    elapsed_time = np.around(1000 * (end - frame_time), decimals=1)
    calc_time = np.around(1000 * (end - start), decimals=1)
    fps = np.around(1.0 / (end - frame_time), decimals=1)

    # draw frame time
    draw_text(frame, f'rtt: {elapsed_time} ms', location, color_map["cyan"], text_size)
    draw_text(frame, f'calc t: {calc_time} ms', (location[0], location[1] + spacing), color_map["cyan"], text_size)
    draw_text(frame, f'FPS: {fps}', (location[0], location[1] + (2 * spacing)), color_map["cyan"], text_size)
