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

class ball_controller:

    p = 0.001
    i = 0.05
    d = 0.0015

    # ESP32 stepper motor interface
    motors = None

    # target to move the ball towards
    target = None

    # velocities
    target_vel = [0, 0]
    vel = [0, 0]
    # window for speed estimation
    window_size = 5
    position_window = []
    # position_window = [None for _ in range(window_size)]
    print(position_window)

    # setup PID, and set setpoint to an error of 0
    x_pid = PID(p, i, d, setpoint=0)
    x_out = 0
    y_pid = PID(p, i, d, setpoint=0)
    y_out = 0
    # output = 0
    output = [0, 0]
    x_pid.sample_time = 1.0 / 120
    y_pid.sample_time = 1.0 / 120

    # p_vel = 0.22
    p_vel = 0.1
    # i_vel = 0.001
    # i_vel = 0.35
    i_vel = 0.45
    # i_vel = 0.01
    d_vel = 0.001
    # d_vel = 0.01

    x_speed = PID(p_vel, i_vel, d_vel, setpoint=0)
    y_speed = PID(p_vel, i_vel, d_vel, setpoint=0)
    x_speed.output_limits = (-0.9, 0.9)
    # x_speed.output_limits = (-1.0, 1.0)
    y_speed.output_limits = (-0.9, 0.9)
    # y_speed.output_limits = (-1.0, 1.0)

    x_speed.sample_time = 1.0 / 120
    y_speed.sample_time = 1.0 / 120


    def __init__(self):
        # set output limits to format ESP-32 driver expects
        self.x_pid.output_limits = (-0.8, 0.8)
        self.y_pid.output_limits = (-0.8, 0.8)

        self.motors = motor_interface()

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.target = (x, y, 25)

    def position_control(self, ball_pos):
        # print(f'{ball_pos}, {self.target}')
        if ball_pos and self.target is not None:
            error = ball_error(ball_pos, self.target)
            if (abs(error[0]) < self.target[2] and abs(error[1]) < self.target[2]):
                self.x_pid.output_limits = (-0.0, 0.0)
                self.y_pid.output_limits = (-0.0, 0.0)
            elif (abs(error[0]) < 45 and abs(error[1]) < 45):
                self.x_pid.output_limits = (-0.3, 0.3)
                self.y_pid.output_limits = (-0.3, 0.3)
            elif (abs(error[0]) < 100 and abs(error[1]) < 100):
                self.x_pid.output_limits = (-0.4, 0.4)
                self.y_pid.output_limits = (-0.4, 0.4)
            else:
                self.x_pid.output_limits = (-0.5, 0.5)
                self.y_pid.output_limits = (-0.5, 0.5)
                

            self.x_out = -self.x_pid(error[0])
            self.y_out = self.y_pid(error[1])
            self.output = [self.x_out, self.y_out]
        else:
            self.output = [0, 0]

    def speed_control(self, ball_pos):
        if ball_pos is not None:
            self.update_speed_estimate(ball_pos)

            # set output from pid to get desired speed
            if self.target_vel is None:
                self.output = [0, 0]
            # elif:
                # error = ball_error(ball_pos, self.)
            else:
                error = self.velocity_error()
                print(f'target velocity: {self.target_vel} velocity error: {error} | current velocity: {self.vel}')
    

                if abs(error[0]) < 0.2:
                    self.x_speed.output_limits = (-0.3, 0.3)
                else:
                    self.x_speed.output_limits = (-0.4, 0.4)
                if abs(error[1]) < 0.2:
                    self.y_speed.output_limits = (-0.3, 0.3)
                else:
                    self.y_speed.output_limits = (-0.4, 0.4)

                # if error[0] < 0.2 and self.vel[0] < 0.1:
                #     self.output[0] = 0
                # else:
                #     self.output[0] = self.x_speed(error[0])

                # if error[1] < 0.2 and self.vel[1] < 0.1:
                #     self.output[1] = 0
                # else:
                #     self.output[1] = self.x_speed(error[1])

                self.output = [self.x_speed(error[0]), self.y_speed(error[1])]
        else:
            self.output = [0, 0]

    def update_speed_estimate(self, ball_pos):
        # if 
        # pop last position from queue
        if len(self.position_window) == self.window_size:
            self.position_window.pop(0)
        self.position_window.append([ball_pos[0], ball_pos[1]])
        # print(self.position_window)
        self.calculate_speed()
        
        # pass

    def calculate_speed(self):
        # print(self.target_vel)
        # print(self.position_window)
        max = np.amax(self.position_window, axis=0)
        min = np.amin(self.position_window, axis=0)
        self.vel = max - min
        # print(self.vel)
        self.vel = self.vel / self.window_size
        # print(self.vel)
        # pass
        

    def velocity_error(self):
        return (round(self.vel[0] - self.target_vel[0], ndigits=2), round(self.vel[1] - self.target_vel[1], ndigits=2))

    def process_update(self, ball_pos):
        self.position_control(ball_pos)
        # self.speed_control(ball_pos)

        self.motors.set_angle_and_send(self.output)

    def set_target(self, target):
        self.target = target

    def set_target_velocity(self, target_velocity):
        self.target_vel = [round(target_velocity[0] * 5, ndigits=2), round(target_velocity[1] * 5, ndigits=2)]

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
    ps4 = ps4_controller()

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

        # c.target_vel = ps4.read_joystick()
        c.set_target_velocity(ps4.read_joystick())
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

        # draw table tilt magnitude where ball is located
        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, c.output, vid_settings['magnitude_scalar'], color_map['brightorange'])

        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, ps4.axis_data, vid_settings['magnitude_scalar'], color_map['green'])
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
