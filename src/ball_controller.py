from os import read
import cv2 as cv
import numpy as np
from webcam import webcam
from feature_detector import detector
from simple_pid import PID
from utils import *
from timeit import default_timer as timer
from motor_interface import motor_interface

# global mouse click pos
mouse_x, mouse_y = -1, -1

class ball_controller:

    p = 0.002
    i = 0.002
    # i = 0
    d = 0
    # d = 0.0005

    # ESP32 stepper motor interface
    motors = None

    # target to move the ball towards
    target = None

    # setup PID, and set setpoint to an error of 0
    x_pid = PID(p, i, d, setpoint=0)
    x_out = 0
    y_pid = PID(p, i, d, setpoint=0)
    y_out = 0
    output = 0
    x_pid.sample_time = 1.0 / 120
    y_pid.sample_time = 1.0 / 120

    def __init__(self):
        # set output limits to format ESP-32 driver expects
        # self.x_pid.output_limits = (-1, 1)
        self.x_pid.output_limits = (-0.8, 0.8)
        # self.y_pid.output_limits = (-1, 1)
        self.y_pid.output_limits = (-0.8, 0.8)

        self.motors = motor_interface()

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.target = (x, y, 25)

    def process_update(self, ball_pos):
        # print(f'{ball_pos}, {self.target}')
        if ball_pos and self.target is not None:
            error = ball_error(ball_pos, self.target)
            # print(error)
            self.x_out = -self.x_pid(error[0])
            self.y_out = self.y_pid(error[1])

        self.output = [self.x_out, self.y_out]

        self.motors.set_angle_and_send(self.output)
        


def main():
    script_desc = 'Interact with ball control realtime via mouse events'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = read_yaml(maze_conf)
    window_name = vid_settings['window_name']

    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)
    c = ball_controller()

    # register mouse click callback
    cv.setMouseCallback(window_name, c.mouse_event)

    # Main loop - object detection and labeling for each video frame
    while True:
        frame_time = timer() # time from when frame was taken

        ### Step 1: Get video frame
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: video frame not loaded.")
            break
        d.frame_count += 1

        start = timer() # time at which frame was ready

        ### Step 2: crop and transform to get final maze image
        # frame = d.crop_and_transform(frame)
        frame = d.crop_no_transform(frame)

        ### Step 3: detect objects
        d.detect_objects(frame)

        #update PID control
        c.process_update(d.ball_pos)

        end = timer() # time after all calculation were completed

        ### Step 4: Draw detected objects and message text to video frame
        d.annotate_ball(frame)

        # draw table tilt magnitude where ball is located
        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, c.output, vid_settings['magnitude_scalar'], color_map['brightorange'])

        # draw error line
        if d.ball_pos and c.target is not None:
            draw_line(frame, (c.target[0], c.target[1]), (d.ball_pos[0], d.ball_pos[1]), BGR_color=color_map['red'])

        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])
        
        # display mouse event to screen
        if c.target is not None:
            draw_circles(frame, [c.target], num=1, BGR_color=color_map['green'])

        ### Step 5: Display video on screen
        cv.imshow(window_name, frame)
        
        ### Step 6: Check for key command
        if cv.waitKey(1) == ord('q'):
            break

    # clean up
    camera.vid.release()
    cv.destroyAllWindows()

    # Print statistics to terminal
    print(f'frames captured: {d.frame_count}')
    print(f"Number of frames where ball was missed: {d.missed_frames_ball}")
    print(f"Ball detection rate: {np.around((1 - d.missed_frames_ball / d.frame_count), decimals=4) * 100}%")



if __name__ == "__main__":
	main()
