# main loop for solving the maze
# create motor interface, ball_controller, and other utils
from motor_interface import motor_interface
from ball_controller import ball_controller
from feature_detector import detector
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

    file = ''

    if maze_conf == config_files['easy']:
        file = path_files['easy']
    if maze_conf == config_files['med']:
        file = path_files['med']
    if maze_conf == config_files['hard']:
        file = path_files['hard']


    p = path(file)
    c = ball_controller()

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
        c.process_update(d.ball_pos)
        if d.ball_pos is not None:
            # print(c.output)
            draw_magnitude(frame, d.ball_pos, c.output, vid_settings['magnitude_scalar'], color_map['brightorange'])

        
        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])

        # update and show path
        if d.ball_pos is not None:
            p.process_update(d.ball_pos)
            c.set_target(p.pts[p.idx])
        p.draw_waypoints(frame, d.ball_pos)

        ### Step 5: Display video on screen
        cv.imshow(window_name, frame)
        
        ### Step 6: Check for exit command
        wait = cv.waitKey(1)
        if wait == ord('q'):
            break
        elif wait == ord('b'):
            p.prev_pt()
        elif wait == ord('n'):
            p.next_pt()

    # clean up
    camera.vid.release()
    cv.destroyAllWindows()

    # Print statistics to terminal
    print(f'frames captured: {d.frame_count}')
    print(f"Number of frames where ball was missed: {d.missed_frames_ball}")
    print(f"Ball detection rate: {np.around((1 - d.missed_frames_ball / d.frame_count), decimals=4) * 100}%")


if __name__ == "__main__":
	main()


def main():
    pass

if __name__ == "__main__":
	main()
