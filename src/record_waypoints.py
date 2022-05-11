# display webcam and take mouse pointer events 
# show chosen points, then all to file

import cv2 as cv
import utils
from webcam import webcam
import yaml
import json

class recorder(object):

    points = []

    def __init__(self, conf) -> None:
        # configure webcam
        self.camera = webcam(conf)
        self.settings = utils.read_yaml(conf)
        self.window_name = self.settings['window_name']

    # return frame from webcam object
    def grab_frame(self):
        return self.camera.read_frame()

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            print(f'{x} : {y}')
            self.append_point((x, y))

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
        utils.draw_circles(frame, self.points, BGR_color=utils.color_map["brightorange"])
        

    def update(self):
        ret, frame = self.grab_frame()
        frame = utils.crop_frame(frame, self.settings['x_frame'], self.settings['y_frame'])

        if not ret:
            return False

        # draw circles
        self.display_points(frame)

        # display frame
        cv.imshow(self.window_name, frame)

        return True


def main():

    # create recorder
    config_file = utils.config_files['camera_1080']
    r = recorder(config_file)

    # setup mouse events
    cv.setMouseCallback(r.window_name, r.mouse_event)

    # monitor webcam, and record waypoints to file
    while True:

        # run 1 frame
        if not r.update():
            print('End of video stream, exiting...')
            break

        if cv.waitKey(1) == ord('q'):
            break

    r.camera.print_camera_settings()
    r.camera.vid.release()
    cv.destroyAllWindows()

    # record waypoints to file
    prefix = 'paths'
    with open(f'{prefix}/path.json', 'w') as file:
        json.dump(r.points, file)


if __name__ == "__main__":
    main()
