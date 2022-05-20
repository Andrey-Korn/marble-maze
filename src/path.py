# queuing system for navigating through our waypoints representing the path through the maze
# logic for timing how long you are at a waypoint, and for drawing the waypoints to the screen
import json
from webcam import webcam
from feature_detector import detector
from utils import *
from timeit import default_timer as timer

class path(object):
    pts = []
    waypoint_range = 0
    idx = 0
    time_at_pt = 0
    finished = False

    def __init__(self, path_file) -> None:
        f = open(path_file, 'r')
        self.pts = json.load(f)

        # grab waypoint radius
        self.waypoint_range = self.pts[0][2]


    # draw all waypoints with color_code
    def draw_waypoints(self, frame, ball_pos):
        # draw first waypoint in green
        draw_circles(frame, self.pts[self.idx:], BGR_color=color_map['green'])
        # draw error line
        if ball_pos is not None:
           draw_line(frame, (self.pts[self.idx][0], self.pts[self.idx][1]), (ball_pos[0], ball_pos[1]), BGR_color=color_map['red'])

        if len(self.pts) > 1:
            draw_circles(frame, self.pts[self.idx + 1:], BGR_color=color_map['orange'], annotate=True)

        if self.finished:
            draw_text(frame, 'winner!', position= (500, 500), BGR_color=color_map['blue'], font_size=3)
        
    def prev_pt(self):
        if self.idx > 0:
            self.idx -= 1

    def next_pt(self):
        if self.idx < len(self.pts) - 1:
            self.idx += 1
    
    # compare ball position and waypoint and progess maze
    def process_update(self, ball_pos):
        # print(f'{len(self.pts)}, {self.idx}')
        if self.idx == len(self.pts) - 1 and self.ball_at_pt(ball_pos):
            self.finished = True

        if self.ball_at_pt(ball_pos) and len(self.pts) - 1 > self.idx:
            self.idx += 1


    def ball_at_pt(self, ball_pos):
        if ball_pos is not None:
            error = ball_error((ball_pos[0], ball_pos[1]), (self.pts[self.idx]))
            return at_target(error, self.waypoint_range)
        return


# display camera feed w/ ball detection and path
def main():
    # setup arguments and parse to get config files
    script_desc = 'Display feature detection to screen'
    args = setup_arg_parser(script_desc)
    vid_conf = args.camera
    maze_conf = args.maze
    vid_settings = read_yaml(vid_conf)
    maze_settings = read_yaml(maze_conf)
    window_name = vid_settings['window_name']

    file = ''

    if maze_conf == config_files['easy']:
        file = path_files['easy']
    if maze_conf == config_files['med']:
        file = path_files['med']
    if maze_conf == config_files['hard']:
        file = path_files['hard']

    p = path(file)
    print(p.pts)
    camera = webcam(vid_settings)
    d = detector(vid_settings, maze_settings)

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
        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time, vid_settings['text_size'])


        # update and show path
        if d.ball_pos is not None:
            p.process_update(d.ball_pos)
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
