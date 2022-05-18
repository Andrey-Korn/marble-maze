import cv2 as cv
import numpy as np
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

def setup_arg_parser(desc, maze_req=True):
    parser = argparse.ArgumentParser(description=desc)
    # get maze config
    parser.add_argument('-m', '--maze', type=int, required=True, nargs=1, 
                        help='specify maze board: (1) easy (2) medium (3) hard')

    # get camera config
    parser.add_argument('-c', '--camera', type=str, nargs=1,
                        help='camera config file')

    args = parser.parse_args()
    if args.camera == None:
        args.camera = config_files['camera_1080']

    if args.maze[0] == 1:
        args.maze = config_files['easy']
    elif args.maze[0] == 2:
        args.maze = config_files['med']
    elif args.maze[0] == 3:
        args.maze = config_files['hard']
    else:
        print('not a valid maze board #!')
        quit()
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

# cv functions
def draw_text(img: np.ndarray, text:str, position: tuple, BGR_color: tuple) -> None:
    """ Draws text of color BGR_color to img at position """
    new_img = cv.putText(img, text, position, cv.FONT_HERSHEY_SIMPLEX, 2, BGR_color, 3)
    img = new_img


def draw_circles(img: np.ndarray, circles: list, num: int = -1, BGR_color: tuple = (0, 0, 255)) -> None:
    """ Draws output from cv.HoughCircles onto img """

    if num == -1:
        num = len(circles)

    for c in circles[:num]:
        cv.circle(img, (c[0],c[1]), c[2], BGR_color, 3)   # Draw circle
        cv.circle(img, (c[0],c[1]), 2, BGR_color, 3)   # Draw dot at circle's center
    return
