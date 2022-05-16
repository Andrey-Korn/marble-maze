from os import error
import cv2 as cv
import numpy as np
from numpy.lib import utils
from webcam import webcam
from timeit import default_timer as timer

from utils import *


# bring in file vs webcam choice

class detector(object):
    fast = None

    # previous corner values
    prev_tl = None 
    prev_tr = None
    prev_bl = None
    prev_br = None

    def __init__(self, conf, ) -> None:

        # read frame size from config file
        self.settings = read_yaml(conf)
        self.height = self.settings['frame_height'][1] - self.settings['frame_height'][0]
        self.width = self.settings['frame_width'][1] - self.settings['frame_width'][0]
        print(f'frame width: {self.width} frame height: {self.height}')

        # setup fast corner detection
        self.fast = cv.FastFeatureDetector_create(threshold=35)
        self.fast.setNonmaxSuppression(0)
        
        # set initial points to use as a corner estimation
        self.prev_tl = (0, 0)
        self.prev_tr = (0, self.width)
        self.prev_bl = (self.height, 0)
        self.prev_br = (self.height, self.width)


    def detect_path(self, img: np.ndarray) -> np.ndarray:
        """
        Detects the path decal on the game board.
        Returns:
            * a contour found using np.findContours()
            * if no matching contour found, returns None 
        """

        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5, 5), 1)

        # # Method 1
        # # adaptive = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 13, 3)
        # canny = cv.Canny(blur, 125, 175)
        # contours, hierarchy = cv.findContours(canny, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)

        # Method 2 (faster and more accurate)
        ret, thresh = cv.threshold(blur, 170, 255, cv.THRESH_BINARY_INV)
        contours, hierarchy = cv.findContours(thresh, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        
        # Draw contours whose centers are close to the expected center of the path
        for cnt in contours:
            
            # Calculate centroid of contour
            M = cv.moments(cnt)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = -1, -1
            
            # near_center = cX > 950 and cX < 970 and cY > 575 and cY < 600  # Used for non-cropped 1080p video
            near_center = cX > 560 and cX < 580 and cY > 480 and cY < 500
            if near_center and cv.arcLength(cnt, True) > 10_000:
                print(cnt)
                return cnt
        return

    def average_corner_keypoints(self, kp):
        
        pts = cv.KeyPoint_convert(kp)
        if len(pts) > 0:
            a = np.array(pts)
            a = np.average(a, axis=0)
            a = np.around(a, decimals=0)
            # print(a)
            return a.astype(int)
        # return np.array[0, 0]
        return None

    # use FAST feature decection w/localized search to find maze corners
    def find_maze_corner(self, src: np.ndarray):

        # process for each corner
        #   crop the frame to a small window, large enough to always see the corner
        #   use FAST corner detect, with desired threshold value from maze config 
        #   take average of points found, to come of with corner estimation in px
        #   o.w. use arbitrary point or prev point

        # crop_frame(src, height_range, width_range)
        # search for top left
        tl_frame = crop_frame(src, (0, 100), (0, 100))
        tl_corner = self.fast.detect(tl_frame, None)
        tl_frame = cv.drawKeypoints(tl_frame, tl_corner, None, color=(255, 0, 0))
        cv.imshow('top_left', tl_frame)
        tl_corner = self.average_corner_keypoints(tl_corner)
        if tl_corner is not None:
            tl_corner = (tl_corner[0], tl_corner[1])
            self.prev_tl = tl_corner
        else:
            tl_corner = self.prev_tl 
        # print(tl_corner)

        # search for top right
        tr_frame = crop_frame(src, (0, 100), (self.width - 100, self.width))
        tr_corner = self.fast.detect(tr_frame, None)
        tr_frame = cv.drawKeypoints(tr_frame, tr_corner, None, color=(255, 0, 0))
        cv.imshow('top_right', tr_frame)
        tr_corner = self.average_corner_keypoints(tr_corner)
        if tr_corner is not None:
            tr_corner = (tr_corner[0], (self.width - 100) + tr_corner[1])
            self.prev_tr = tr_corner
        else:
            tr_corner = self.prev_tr
            
        # print(tr_corner)

        # search for bot left
        bl_frame = crop_frame(src, (self.height - 100, self.height), (0, 100))
        bl_corner = self.fast.detect(bl_frame, None)
        bl_frame = cv.drawKeypoints(bl_frame, bl_corner, None, color=(255, 0, 0))
        cv.imshow('bot_left', bl_frame)
        bl_corner = self.average_corner_keypoints(bl_corner)
        if bl_corner is not None:
            bl_corner = ((self.height - 100) + bl_corner[0], bl_corner[1])
            self.prev_bl = bl_corner
        else:
            # bl_corner = (self.height, 0)
            bl_corner = self.prev_bl
        # print(bl_corner)

        # search for bot right
        br_frame = crop_frame(src, (self.height - 100, self.height), (self.width - 120, self.width))
        br_corner = self.fast.detect(br_frame, None)
        br_frame = cv.drawKeypoints(br_frame, br_corner, None, color=(255, 0, 0))
        cv.imshow('bot_right', br_frame)
        br_corner = self.average_corner_keypoints(br_corner)
        if br_corner is not None:
            br_corner = ((self.height - 100) + br_corner[0], (self.width - 120) + br_corner[1])
            self.prev_br
        else:
            # br_corner = (self.height, self.width)
            br_corner = self.prev_br
        # print(br_corner)

        
        # return [tl_corner, tr_corner, bl_corner, br_corner]
        return np.array([tl_corner, tr_corner, bl_corner, br_corner], np.float32)


    # transform frame based on detected corners
    def perspective_transform(self, src: np.ndarray, pts):
        # tl, tr, bl, br
        # [h, w]
        dest_pts = np.array([[0, 0], [0, self.width], [self.height, 0], [self.height, self.width]], np.float32)
        print(pts)
        print(dest_pts)
        matrix = cv.getPerspectiveTransform(pts, dest_pts)
        result = cv.warpPerspective(src, matrix, (self.width, self.height))
        return result


    def erode_and_dilate(self, src: np.ndarray, kernel_size: int, iterations: int = 1) -> np.ndarray:
        """ Performs a series of erosions followed by dilations on src image """
        
        erosion_kernel = np.ones((  kernel_size, kernel_size), np.uint8)
        dilation_kernel = (         kernel_size, kernel_size)

        while iterations:
            eroded = cv.erode(src, erosion_kernel, iterations=1)
            src = cv.dilate(eroded, dilation_kernel, iterations=1)
            iterations -= 1

        return src


    def detect_blue_ball(self, src: np.ndarray) -> tuple:
        """ 
        Detects the blue ball in an image. 
        Returns: 
            * tuple (x, y, rad)
            * if no ball detected, returns None
        """
        blur = cv.GaussianBlur(src, (7, 7), cv.BORDER_DEFAULT)
        blue_channel = blur[:,:,0]
        ret, green_mask = cv.threshold(blur[:,:,1], 50, 255, cv.THRESH_BINARY_INV)
        ret, red_mask = cv.threshold(blur[:,:,2], 15, 255, cv.THRESH_BINARY_INV)
        masked = cv.inRange(blue_channel, 20, 150)
        no_green = cv.bitwise_and(masked, masked, mask=green_mask)
        no_red = cv.bitwise_and(masked, masked, mask=red_mask)
        no_green_red = cv.bitwise_and(no_green, no_green, mask=no_red)

        kernel = np.ones((3,3), np.uint8)
        eroded_dilated = self.erode_and_dilate(no_green_red, 5)
        # eroded_dilated = erode_and_dilate(no_green_red, 1)

        # uncomment to see ball segmentation
        # cv.imshow('ball_mask', eroded_dilated)

        # method 2: min enclosing circle
        # circles = []
        contours, hierarchy = cv.findContours(eroded_dilated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        for c in contours:
            (x,y), r = cv.minEnclosingCircle(c)
            # reject contours that do not meet ball radius
            if r > self.settings['ball_radius'][0] and r < self.settings['ball_radius'][1]:
                # circles.append((x, y, r))
                # print(f'x: {x} y: {y} r: {r}')
                return [int(x), int(y), int(r)]

        return None

        # Method 1: Hough Circles 
        # final_image = eroded_dilated
        # circles = cv.HoughCircles(final_image, cv.HOUGH_GRADIENT, 1, 50, param1=30, param2=15, minRadius=2, maxRadius=50)
        # if circles is not None:
            # circles = np.uint16(np.around(circles))
            # ball = circles[0,:][0]
            # print(ball)
            # return (
                # ball[0],
                # ball[1],
                # ball[2]
            # )
        # else:
            # return None

# timer vars
frame_time = 0
start = 0
end = 0
elapsed_time = 0
calc_time = 0

def main():
    script_desc = 'Display feature detection to screen'
    args = setup_arg_parser(script_desc)
    # Open video feed/file
    video_path = video_path_map["blue_bright"]
    conf = args.camera
    # conf = config_files['camera_1080']
    camera = webcam(conf)
    settings = read_yaml(conf)
    # maze_conf = read_yaml(args.maze[0])
    window_name = settings['window_name']
 
    d = detector(conf)


    # Variables for recording detected object state
    path, ball_pos = None, None

    # For calculating statistics (object detection accuracy, framerate)
    frame_count = 0
    missed_frames_ball = 0

    # Main loop - object detection and labeling for each video frame
    while camera.vid.isOpened():

        frame_time = timer()
        ### Step 1: Get video frame
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: video frame not loaded.")
            break
        frame_count += 1

        start = timer()

        # Crop video frame to only desired area
        frame = crop_frame(frame, settings['frame_height'], settings['frame_width'])

        # perspective transform
        points = d.find_maze_corner(frame)
        # print(points)
        frame = d.perspective_transform(frame, points)


        ### STEP 2: Detect objects

        ## 2.1: Path
        # Find current path outline/contour (only every 3rd frame)
        # if frame_count % 3 == 0:
        #     new_path = detect_path(frame)
        #     if new_path is not None:
        #         path = new_path

        ## 2.2: Ball
        # Find current ball position
        if ball_pos is None:    # If ball was not detected during last cycle, search entire video frame
            ball_pos = d.detect_blue_ball(frame)
        else:                   # If ball was detected last cycle, search only the area surrounding the most recently recorded ball position
            area_size = 100
            x_min_offset = min(0, ball_pos[0] - area_size)
            y_min_offset = min(0, ball_pos[1] - area_size)
            x_min, x_max = max(0, ball_pos[0] - area_size), ball_pos[0] + area_size
            y_min, y_max = max(0, ball_pos[1] - area_size), ball_pos[1] + area_size
            new_ball_pos = d.detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
            
            # If a ball was successfully detected near prior ball position, calculates new ball position from relative coordinates
            if new_ball_pos is not None:
                new_ball_pos = (
                    max(0, new_ball_pos[0] + ball_pos[0] - area_size - x_min_offset), 
                    max(0, new_ball_pos[1] + ball_pos[1] - area_size - y_min_offset),
                    new_ball_pos[2]
                )
            ball_pos = new_ball_pos

        # If ball not found during this cycle, tally a detection failure (currently stops at frame 769, as this is when the ball falls into a hole in the training video)
        # if ball_pos is None and frame_count < 769:
        if ball_pos is None:
            missed_frames_ball += 1

        end = timer()


        ### STEP 3: Draw detected objects and message text to video frame
        
        # Draw path
        if path is not None:
            cv.drawContours(frame, path, -1, color_map["orange"], 2)

        # Draw ball position and message text
        if ball_pos is not None:
            msg, msg_color = "Ball detected", "green"
            draw_circles(frame, [ball_pos], BGR_color=color_map["magenta"])
            draw_text(frame, f"Position (X, Y): {ball_pos[0]}, {ball_pos[1]}", (100, 200), color_map["green"])
        else:
            msg, msg_color = "Ball NOT detected", "red"
        draw_text(frame, msg, (100, 100), color_map[msg_color])

        elapsed_time = np.around(1000 * (end - frame_time), decimals=1)
        calc_time = np.around(1000 * (end - start), decimals=1)

        # draw frame time
        draw_text(frame, f'rtt: {elapsed_time} ms', (700, 800), color_map["cyan"])
        draw_text(frame, f'calc t: {calc_time} ms', (700, 900), color_map["cyan"])

        # print(elapsed_time)


        ### Step 4: Display video on screen
        cv.imshow(window_name, frame)
        
        ### Step 5: Check for exit command
        if cv.waitKey(1) == ord('q'):
            break

    camera.vid.release()
    cv.destroyAllWindows()

    # Print statistics to terminal
    print(f"Number of frames where ball was missed: {missed_frames_ball}")
    print(f"Ball detection rate: {np.around((1 - missed_frames_ball / frame_count), decimals=4) * 100}%")


if __name__ == "__main__":
	main()
