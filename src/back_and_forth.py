
from webcam import webcam
from feature_detector import detector
from position_controller import position_controller
from path import path
from logger import logger
from utils import *
from timeit import default_timer as timer


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
    file = args.path
    p = path(file, t=5, cycle=True)
    l = logger()

    time_begin = timer()

    n = 10

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
        frame, pts = d.crop_and_transform(frame)
        # frame, pts = d.crop_no_transform(frame)

        ### Step 3: detect objects
        d.detect_objects(frame)

        #update PID control
        c.process_update(d.ball_pos)
        if d.ball_pos is not None:
            # print(c.output)
            draw_magnitude(frame, d.ball_pos, c.output, vid_settings['magnitude_scalar'], color_map['brightorange'])

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

        if pts is not None:
            draw_corners(frame, pts)

        # update and show path
        if d.ball_pos is not None:
            p.process_update(d.ball_pos)
            c.set_target(p.pts[p.idx])
        p.draw_waypoints(frame, d.ball_pos)

        ### Step 5: Display video on screen
        cv.imshow(window_name, frame)
        
        ### log for later graphing
        if d.ball_pos and c.target is not None:
            # l.log_new_data(d.ball_pos, c.target, np.round(end - time_begin, 2))
            l.log_new_data(d.ball_pos, c.target, np.round(end - time_begin, 2), d.noisy_ball_pos)

        ### Step 6: Check for key command
        if cv.waitKey(1) == ord('q'):
            break

        if p.n >= n:
            break

    # clean up
    camera.vid.release()
    cv.destroyAllWindows()

    # write logs
    l.write_log()

    # Print statistics to terminal
    print(f'frames captured: {d.frame_count}')
    print(f"Number of frames where ball was missed: {d.missed_frames_ball}")
    print(f"Ball detection rate: {np.around((1 - d.missed_frames_ball / d.frame_count), decimals=4) * 100}%")

if __name__ == "__main__":
	main()
