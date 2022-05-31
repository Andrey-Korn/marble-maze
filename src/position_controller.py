import cv2 as cv
import numpy as np
from webcam import webcam
from feature_detector import detector
from motor_interface import motor_interface
# from ps4_controller import ps4_controller
from simple_pid import PID
from timeit import default_timer as timer
from utils import *

# global mouse click pos
mouse_x, mouse_y = -1, -1

class position_controller:

    x_pid, y_pid = None, None   # PID controllers

    # PID constants for x and y axes
    px, ix, dx, py, iy, dy = 0, 0, 0, 0, 0, 0

    output = [0, 0] # initial target angle
    target = None   # target to move the ball towards
    motors = None   # ESP32 stepper motor interface


    def __init__(self, vid_settings, maze_settings):

        # set yaml parameters
        self.px = maze_settings['x_pid_pos'][0]
        self.ix = maze_settings['x_pid_pos'][1]
        self.dx = maze_settings['x_pid_pos'][2]
        self.py = maze_settings['y_pid_pos'][0]
        self.iy = maze_settings['y_pid_pos'][1]
        self.dy = maze_settings['y_pid_pos'][2]

        # PID output limits from yaml
        self.big_lim = maze_settings['pos_lim_big']
        self.med_lim = maze_settings['pos_lim_med']
        self.sml_lim = maze_settings['pos_lim_sml']

        self.fps = vid_settings['fps']

        # setup PID, w/ error setpoint of 0
        self.x_pid = PID(self.px, self.ix, self.dx, setpoint=0)
        self.y_pid = PID(self.py, self.iy, self.dy, setpoint=0)
        self.x_pid.sample_time = 1.0 / self.fps
        self.y_pid.sample_time = 1.0 / self.fps

        # set output limits to format ESP-32 driver expects
        self.set_pid_lim(self.big_lim)

        # create ESP32 motor UART connection
        self.motors = motor_interface()


    def position_control(self, ball_pos):
        # print(f'{ball_pos}, {self.target}')
        if ball_pos and self.target is not None:
            error = ball_error(ball_pos, self.target)
            print(error)

            # set appropriate limits
            if abs(error[0]) < 20:
                self.set_x_pid_lim(0)
            elif abs(error[0]) < 40:
                self.set_y_pid_lim(self.sml_lim)
            elif abs(error[0]) < 60:
                self.set_x_pid_lim(self.med_lim)
            else:
                self.set_x_pid_lim(self.big_lim)

            if abs(error[1]) < 20:
                self.set_y_pid_lim(0)
            elif abs(error[1]) < 40:
                self.set_y_pid_lim(self.sml_lim)
            elif abs(error[1]) < 60:
                self.set_y_pid_lim(self.med_lim)
            else:
                self.set_y_pid_lim(self.big_lim)

                
            self.output = [-self.x_pid(error[0]), self.y_pid(error[1])]
        else:
            self.output = [0, 0]


    def set_x_pid_lim(self, lim):
        self.x_pid.output_limits = (-lim, lim)

    def set_y_pid_lim(self, lim):
        self.y_pid.output_limits = (-lim, lim)

    def set_pid_lim(self, lim):
        self.x_pid.output_limits = (-lim, lim)
        self.y_pid.output_limits = (-lim, lim)

    def set_target(self, target):
        self.target = target

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.target = (x, y, 25)

    def process_update(self, ball_pos):
        self.position_control(ball_pos)                 # set output from PID controllers
        self.motors.set_angle_and_send(self.output)     # send target angle to ESP32



def main():
    script_desc = 'Interact with ball position control realtime via mouse events'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = read_yaml(maze_conf)
    window_name = vid_settings['window_name']

    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)
    c = position_controller(vid_settings, maze_settings)
    # ps4 = ps4_controller()

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
        # frame, pts = d.crop_and_transform(frame)
        frame, pts = d.crop_no_transform(frame)

        ### Step 3: detect objects
        d.detect_objects(frame)

        #update PID control
        c.process_update(d.ball_pos)

        end = timer() # time after all calculation were completed

        ### Step 4: Draw detected objects and message text to video frame
        d.annotate_ball(frame)

        # draw table tilt target output where ball is located
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
