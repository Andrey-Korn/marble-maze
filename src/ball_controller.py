from os import read
import cv2 as cv
import numpy as np
from webcam import webcam
from feature_detector import detector
from simple_pid import PID
from utils import *
from timeit import default_timer as timer

# global mouse click pos
mouse_x, mouse_y = -1, -1

class ball_controller:

    # target to move the ball towards
    target = None

    def __init__(self):
        pass

    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.target = (x, y, 25)

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

        end = timer() # time after all calculation were completed

        ### Step 4: Draw detected objects and message text to video frame
        d.annotate_ball(frame)

        # draw table tilt magnitude where ball is located
        # if d.ball_pos is not None:
            # draw_magnitude(frame, d.ball_pos, ps4.axis_data, vid_settings['magnitude_scalar'], color_map['brightorange'])

        # draw error line
        if d.ball_pos and c.target is not None:
            draw_line(frame, (c.target[0], c.target[1]), (d.ball_pos[0], d.ball_pos[1]), BGR_color=color_map['red'])

        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])
        
        # display mouse event to screen
        if c.target is not None:
            draw_circles(frame, [c.target], num=1, BGR_color=color_map['green'])

        ### Step 5: Display video on screen
        cv.imshow(window_name, frame)
        
        ### Step 6: Check for exit command
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
