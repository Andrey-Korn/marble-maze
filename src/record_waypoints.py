# display webcam and take mouse pointer events 
# show chosen points, then all to file

import cv2 as cv
from utils import *
from webcam import webcam
from feature_detector import detector
import json

class recorder(object):

    d = None
    points = []

    def __init__(self, settings) -> None:
        self.settings = settings

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            print(f'{x} : {y}')
            self.append_point((x, y, 25))

        # if event == cv.EVENT_RBUTTONDOWN:
        if event == cv.EVENT_MBUTTONDOWN:
            self.dequeue_point()

    def append_point(self, pt):
        self.points.append(pt)

    def dequeue_point(self):
        if len(self.points) > 0:
            self.points.pop(0)
        # print(self.points)

    # draw circles where points were placed
    def display_points(self, frame):
        draw_circles(frame, self.points, BGR_color=color_map["brightorange"])


def main():

    # setup arguments and parse to get config files
    script_desc = 'Display feature detection to screen'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = read_yaml(maze_conf)
    window_name = vid_settings['window_name']

    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)
    r = recorder(vid_settings)

    # setup mouse events
    cv.setMouseCallback(window_name, r.mouse_event)

    # monitor webcam, and record waypoints to file
    while True:

        # get camera frame and crop down to usable area
        ret, frame = camera.read_frame()
        if not ret:
            print('End of video stream, exiting...')
            break
        frame = crop_frame(frame, vid_settings['frame_height'], vid_settings['frame_width'])

        # draw circles
        r.display_points(frame)

        # display frame
        cv.imshow(window_name, frame)

        if cv.waitKey(1) == ord('q'):
            break

    camera.print_camera_settings()
    camera.vid.release()
    cv.destroyAllWindows()

    # record waypoints to file
    prefix = 'paths'
    with open(f'{prefix}/path.json', 'w') as file:
        json.dump(r.points, file)


if __name__ == "__main__":
    main()
