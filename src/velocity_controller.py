from os import read
import cv2 as cv
import numpy as np
from webcam import webcam
from feature_detector import detector
from ps4_controller import ps4_controller
from simple_pid import PID
from utils import *
from timeit import default_timer as timer
from motor_interface import motor_interface

# global mouse click pos
mouse_x, mouse_y = -1, -1

class velocity_controller:

    x_pid, y_pid = None, None   # PID controllers

    # PID constants for x and y axes
    px, ix, dx, py, iy, dy = 0, 0, 0, 0, 0, 0

    vel = [0, 0]        # velocity measurement
    target = [0, 0]     # initial target velocity
    motors = None       # ESP32 stepper motor interface

    # velocity estimation
    window_size = 4
    position_window = []


    def __init__(self, vid_settings, maze_settings):

        # set yaml parameters
        self.px = maze_settings['x_pid_vel'][0]
        self.ix = maze_settings['x_pid_vel'][1]
        self.dx = maze_settings['x_pid_vel'][2]
        self.py = maze_settings['y_pid_vel'][0]
        self.iy = maze_settings['y_pid_vel'][1]
        self.dy = maze_settings['y_pid_vel'][2]

        # PID output limits from yaml
        self.big_lim = maze_settings['vel_lim_big']
        self.med_lim = maze_settings['vel_lim_med']
        self.sml_lim = maze_settings['vel_lim_sml']

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

    # def mouse_event(self, event, x, y, flags, param):
    #     if event == cv.EVENT_LBUTTONDOWN:
    #         self.target = (x, y, 25)


    def speed_control(self, ball_pos, kf=False):
        if ball_pos is not None:
            # self.update_speed_estimate(ball_pos)
            self.update_speed_from_kf(kf)

            # set output from pid to get desired speed
            if self.target is None:
                self.output = [0, 0]
            else:
                error = self.velocity_error()
                print(f'target velocity: {self.target} velocity error: {error} | current velocity: {self.vel}')

                # if abs(error[0]) < 0.2:
                #     self.x_pid.output_limits = (-0.1, 0.1)
                # else:
                #     self.x_pid.output_limits = (-0.3, 0.3)
                # if abs(error[1]) < 0.2:
                #     self.y_pid.output_limits = (-0.1, 0.1)
                # else:
                #     self.y_pid.output_limits = (-0.3, 0.3)

                raw_output = [self.x_pid(error[0]), self.y_pid(error[1])]
                self.output = normalize_magnitudes(raw_output)
        else:
            self.output = [0, 0]

    def update_speed_from_kf(self, kf):
        # print(kf)
        self.vel = [round(kf.x[2]), round(kf.x[3])]

    def update_speed_estimate(self, ball_pos):
        # pop last position from queue
        if len(self.position_window) == self.window_size:
            self.position_window.pop(0)
        self.position_window.append([ball_pos[0], ball_pos[1]])
        # print(self.position_window)
        self.calculate_speed()

    def calculate_speed(self):
        # print(self.target_vel)
        # print(self.position_window)
        max = np.amax(self.position_window, axis=0)
        min = np.amin(self.position_window, axis=0)
        self.vel = (max - min) / self.window_size
        # self.vel = self.vel / self.window_size
        # print(self.vel)

    def x_set_pid_lim(self, lim):
        self.x_pid.output_limits = (-lim, lim)

    def y_set_pid_lim(self, lim):
        self.y_pid.output_limits = (-lim, lim)

    def set_pid_lim(self, lim):
        self.x_pid.output_limits = (-lim, lim)
        self.y_pid.output_limits = (-lim, lim)   

    def velocity_error(self):
        return (round(self.vel[0] - self.target[0], ndigits=2), round(self.vel[1] - self.target[1], ndigits=2))

    def set_target_velocity(self, target_velocity):
        self.target = [round(target_velocity[0] * 5, ndigits=2), round(target_velocity[1] * 5, ndigits=2)]

    def process_update(self, ball_pos, kf):
        self.speed_control(ball_pos, kf)
        self.motors.set_angle_and_send(self.output)


def main():
    script_desc = 'Interact with ball velocity control realtime via controller joystick'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = read_yaml(maze_conf)
    window_name = vid_settings['window_name']

    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)
    c = velocity_controller(vid_settings, maze_settings)
    ps4 = ps4_controller()

    # Main loop - object detection and labeling for each video frame
    while True:
        frame_time = timer() # time from when frame was taken

        ### Step 1: Get video frame
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: video frame not loaded.")
            break
        d.frame_count += 1

        c.set_target_velocity(ps4.read_joystick())
        start = timer() # time at which frame was ready

        ### Step 2: crop and transform to get final maze image
        frame, pts = d.crop_and_transform(frame)
        # frame, pts = d.crop_no_transform(frame)

        ### Step 3: detect objects
        if frame is not None:
            d.detect_objects(frame)

        #update PID control
        c.process_update(d.ball_pos, d.kf)

        end = timer() # time after all calculation were completed

        ### Step 4: Draw detected objects and message text to video frame
        d.annotate_ball(frame)

        # draw table tilt magnitude where ball is located
        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, c.output, vid_settings['magnitude_scalar'], color_map['brightorange'])

        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, ps4.axis_data, vid_settings['magnitude_scalar'], color_map['green'])

        # draw error line
        # if d.ball_pos and c.target is not None:
            # draw_line(frame, (c.target[0], c.target[1]), (d.ball_pos[0], d.ball_pos[1]), BGR_color=color_map['red'])

        if frame is not None:
            display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])
        
        # display mouse event to screen
        # if c.target is not None:
            # draw_circles(frame, [c.target], num=1, BGR_color=color_map['green'])

        ### Step 5: Display video on screen
        if frame is not None:
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
