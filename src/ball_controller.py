import cv2 as cv
import numpy as np
import webcam
import yaml
import argparse
import utils

# global mouse click pos
mouse_x, mouse_y = -1, -1

class ball_controller:
    # detected oject states
    path, ball_pos = None, None

    # target to move the ball towards
    target = None
    target_range = 20

    # frame stats
    frame_count, missed_frames_ball = 0, 0

    def __init__(self, config_file=None):
        self.parser = argparse.ArgumentParser(description='Monitor or record a webcam feed.')
        self.parser.add_argument('--config', 
                                 help='change camera config file')
        self.args = self.parser.parse_args()
        
        # configure webcam
        config_file = 'camera_config_1080.yaml' 
        if self.args.config is not None:
            config_file = self.args.config

        self.camera = webcam.webcam(config_file)


    def mouse_event(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            # print('got here!')
            self.target = (x, y, 1)

    def at_target(self):
        return (abs(self.error[0]) < self.target_range and abs(self.error[1]) < self.target_range)
        

    def update(self):
        ret, frame = c.camera.vid.read()
        self.frame_count += 1

        # crop video frame
        frame = frame[100:1080, 390:1560, :]

        # Find current ball position
        if self.ball_pos is None:    # If ball was not detected during last cycle, search entire video frame
            self.ball_pos = utils.detect_blue_ball(frame)
        else:                   # If ball was detected last cycle, search only the area surrounding the most recently recorded ball position
            area_size = 100
            x_min_offset = min(0, self.ball_pos[0] - area_size)
            y_min_offset = min(0, self.ball_pos[1] - area_size)
            x_min, x_max = max(0, self.ball_pos[0] - area_size), self.ball_pos[0] + area_size
            y_min, y_max = max(0, self.ball_pos[1] - area_size), self.ball_pos[1] + area_size
            new_ball_pos = utils.detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
            
            # If a ball was successfully detected near prior ball position, calculates new ball position from relative coordinates
            if new_ball_pos is not None:
                new_ball_pos = (
                    max(0, new_ball_pos[0] + self.ball_pos[0] - area_size - x_min_offset), 
                    max(0, new_ball_pos[1] + self.ball_pos[1] - area_size - y_min_offset),
                    new_ball_pos[2]
                )
            self.ball_pos = new_ball_pos

        # count missed ball frames
        if self.ball_pos is None:
            self.missed_frames_ball += 1

        if self.ball_pos is not None:
            msg, msg_color = "Ball detected", "green"
            utils.draw_circles(frame, [self.ball_pos], BGR_color=utils.color_map["magenta"])
            utils.draw_text(frame, f"position (X, Y): {self.ball_pos[0]}, {self.ball_pos[1]}", (100, 200), utils.color_map["green"])
        else:
            msg, msg_color = "Ball NOT detected", "red"
            utils.draw_text(frame, msg, (100, 100), utils.color_map[msg_color])

        # calculate and draw error
        if self.target is not None:
            self.error = utils.ball_error(self.ball_pos, self.target)
            utils.draw_circles(frame, [self.target], BGR_color=utils.color_map["brightorange"])
            # cv.line(frame, self.ball_pos[0:1], self.target[0:1], utils.color_map["brightorange"])

            utils.draw_text(frame, f"target (X, Y): {self.target[0]}, {self.target[1]}", (100, 800), utils.color_map["blue"])
            utils.draw_text(frame, f"error (X, Y): {self.error[0]}, {self.error[1]}", (100, 900), utils.color_map["cyan"])
            if self.at_target():
                utils.draw_text(frame, "at target!", (50, 100), utils.color_map["green"])

 
        # display frame
        cv.imshow(self.camera.window_name, frame)


# create controller
c = ball_controller()

while True:
    # register mouse click callback
    cv.setMouseCallback(c.camera.window_name, c.mouse_event)

    # run 1 frame
    c.update()

    if cv.waitKey(1) == ord('q'):
        break

c.camera.vid.release()
cv.destroyAllWindows()

# Print statistics to terminal
print(f"Number of frames where ball was missed: {c.missed_frames_ball}")
print(f"Ball detection rate: {np.around((1 - c.missed_frames_ball / c.frame_count), decimals=4) * 100}%")
