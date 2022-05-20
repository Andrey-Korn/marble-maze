# main loop for solving the maze manually with a ps4 controller
# create motor interface, ball_controller, and other utils

# import classes
from motor_interface import motor_interface
from ball_controller import ball_controller
from feature_detector import detector
from ps4_controller import ps4_controller
from webcam import webcam
from path import path
from utils import *
from timeit import default_timer as timer

# timer vars
frame_time = 0
start = 0
end = 0

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
    ps4 = ps4_controller()

    file = ''

    if maze_conf == config_files['easy']:
        file = path_files['easy']
    if maze_conf == config_files['med']:
        file = path_files['med']
    if maze_conf == config_files['hard']:
        file = path_files['hard']


    p = path(file)

    # Main loop - object detection and labeling for each video frame
    while True:
        frame_time = timer() # time from when frame was taken

        ### Step 1: Get video frame
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: video frame not loaded.")
            break
        d.frame_count += 1

        # control table via ps4 controller
        ps4.read_joystick()
        ps4.set_new_target()

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
        if d.ball_pos is not None:
            draw_magnitude(frame, d.ball_pos, ps4.axis_data, vid_settings['magnitude_scalar'], color_map['brightorange'])
        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])

        p.process_update(d.ball_pos)
        p.draw_waypoints(frame, d.ball_pos)

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

