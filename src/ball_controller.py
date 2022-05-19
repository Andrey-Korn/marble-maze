import cv2 as cv
import numpy as np
import webcam
from feature_detector import detector
from simple_pid import PID
from utils import *

# global mouse click pos
mouse_x, mouse_y = -1, -1

class ball_controller:
    # detected oject states
    path, ball_pos = None, None

    # target to move the ball towards
    target = None
    target_range = 20

    # frame stats
    frame_count, missed_frames_ball = 0, 0

    def __init__(self, config_file=None):
        pass

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.target = (x, y, 1)

def main():
    script_desc = 'Interact with ball control realtime via mouse events'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = vid_settings(maze_conf)
    window_name = vid_settings['window_name']

    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)
    c = ball_controller()

    # register mouse click callback
    cv.setMouseCallback(c.camera.window_name, c.mouse_event)

    while True:

        # run 1 frame


        if cv.waitKey(1) == ord('q'):
            break

    c.camera.vid.release()
    cv.destroyAllWindows()

    # Print statistics to terminal
    print(f"Number of frames where ball was missed: {c.missed_frames_ball}")
    print(f"Ball detection rate: {np.around((1 - c.missed_frames_ball / c.frame_count), decimals=4) * 100}%")


if __name__ == "__main__":
	main()
