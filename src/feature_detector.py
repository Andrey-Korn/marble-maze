from os import stat
import cv2 as cv
import numpy as np
from webcam import webcam
from timeit import default_timer as timer

from utils import *


# bring in file vs webcam choice

class detector(object):
    # corner detector
    fast = None

    # previous corner values
    prev_tl = None 
    prev_tr = None
    prev_bl = None
    prev_br = None

    # detected objects
    path, ball_pos = None, None

    # For calculating statistics (object detection accuracy, framerate)
    frame_count = 0
    missed_frames_ball = 0

    def __init__(self, vid_settings, maze_settings) -> None:

        # read frame size from config file
        # self.settings = read_yaml(conf)
        self.settings = vid_settings
        self.height = self.settings['frame_height'][1] - self.settings['frame_height'][0]
        self.width = self.settings['frame_width'][1] - self.settings['frame_width'][0]
        print(f'frame width: {self.width} frame height: {self.height}')

        # setup fast corner detection
        self.fast = cv.FastFeatureDetector_create(threshold=25)
        self.fast.setNonmaxSuppression(0)
        
        # set initial points to use as a corner estimation
        self.prev_tl = (0, 0)
        self.prev_tr = (0, self.width)
        self.prev_bl = (self.height, 0)
        self.prev_br = (self.height, self.width)

        # corner filtering
        self.med_offset = self.settings['median_offset']
        self.offsets = self.settings['offsets']

        # search area when ball already known
        self.area_size = self.settings['search_area']

        # annotated text locations
        self.text_tl = (self.settings['text_tl'][0], self.settings['text_tl'][1])
        self.text_tr = (self.settings['text_tr'][0], self.settings['text_tr'][1])
        self.text_spacing = self.settings['text_spacing']


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

    def valid_keypoint(self, median, value) -> bool:
        return (
            (median[0] - self.med_offset < value[0] < median[0] + self.med_offset) and
            (median[1] - self.med_offset < value[1] < median[1] + self.med_offset) )


    def filter_corner(self, kp):
        pts = cv.KeyPoint_convert(kp)
        if len(pts) > 0:
            a = np.array(pts)
            print(f'points\n-------\n{a}\n')
            # print(f'{a[:,0]} {a[:,1]}')
            h = np.median(a[:,0], axis=0)
            w = np.median(a[:,1], axis=0)
            median = np.array([h, w]).astype(int)
            print(f'median: {median}')

            remove_idxs = []
            i = 0
            for _ in a:
                # print(a[i][0])
                # print(a[i][1])
                if not self.valid_keypoint(median, a[i]):
                    remove_idxs.append(i)
                i += 1

            print(f'idx\'s to remove: {remove_idxs}')
            if len(remove_idxs) < len(a):
                a = np.delete(a, remove_idxs, axis=0)
            # a = np.average(a, axis=0).astype(int)

            h = np.median(a[:,0], axis=0)
            w = np.median(a[:,1], axis=0)
            a = np.array([h, w]).astype(int)
            print(f'result: {a}')
            return a
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
        print('\n-----------------------\nTOP LEFT\n-----------------------\n')
        tl_frame = crop_frame(src, (0, self.offsets[0]), (0, self.offsets[0]))
        tl_corner = self.fast.detect(tl_frame, None)
        tl_frame = cv.drawKeypoints(tl_frame, tl_corner, None, color=(255, 0, 0))
        cv.imshow('top_left', tl_frame)
        tl_corner = self.filter_corner(tl_corner)
        if tl_corner is not None:
            tl_corner = (tl_corner[0], tl_corner[1])
            self.prev_tl = tl_corner
        else:
            tl_corner = self.prev_tl 
        # print(tl_corner)

        # search for top right
        print('\n-----------------------\nTOP RIGHT\n-----------------------\n')
        tr_frame = crop_frame(src, (0, self.offsets[4]), (self.width - self.offsets[1], self.width))
        tr_corner = self.fast.detect(tr_frame, None)
        tr_frame = cv.drawKeypoints(tr_frame, tr_corner, None, color=(255, 0, 0))
        cv.imshow('top_right', tr_frame)
        tr_corner = self.filter_corner(tr_corner)
        if tr_corner is not None:
            tr_corner = (tr_corner[0], (self.width - self.offsets[1]) + tr_corner[1])
            self.prev_tr = tr_corner
        else:
            tr_corner = self.prev_tr
        # print(tr_corner)

        # search for bot left
        print('\n-----------------------\nBOT LEFT\n-----------------------\n')
        bl_frame = crop_frame(src, (self.height - self.offsets[0], self.height), (0, self.offsets[0]))
        bl_corner = self.fast.detect(bl_frame, None)
        bl_frame = cv.drawKeypoints(bl_frame, bl_corner, None, color=(255, 0, 0))
        cv.imshow('bot_left', bl_frame)
        bl_corner = self.filter_corner(bl_corner)
        if bl_corner is not None:
            bl_corner = ((self.height - self.offsets[0]) + bl_corner[0], bl_corner[1])
            self.prev_bl = bl_corner
        else:
            bl_corner = self.prev_bl
        # print(bl_corner)

        # search for bot right
        print('\n-----------------------\nBOT LEFT\n-----------------------\n')
        br_frame = crop_frame(src, (self.height - self.offsets[0], self.height), (self.width - self.offsets[3], self.width))
        br_corner = self.fast.detect(br_frame, None)
        br_frame = cv.drawKeypoints(br_frame, br_corner, None, color=(255, 0, 0))
        cv.imshow('bot_right', br_frame)
        br_corner = self.filter_corner(br_corner)
        if br_corner is not None:
            br_corner = ((self.height - self.offsets[0]) + br_corner[0], (self.width - self.offsets[3]) + br_corner[1])
            self.prev_br
        else:
            br_corner = self.prev_br
        # print(br_corner)

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
        eroded_dilated = self.erode_and_dilate(no_green_red, 3)
        # eroded_dilated = erode_and_dilate(no_green_red, 1)

        # uncomment to see ball segmentation
        cv.imshow('ball_mask', eroded_dilated)

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

    def crop_no_transform(self, frame):
        return crop_frame(frame, self.settings['frame_height'], self.settings['frame_width'])

    def crop_and_transform(self, frame):
        # Crop video frame to only desired area
        frame = crop_frame(frame, self.settings['frame_height'], self.settings['frame_width'])

        # perspective transform
        points = self.find_maze_corner(frame)
        frame = self.perspective_transform(frame, points)
        return frame

    def detect_objects(self, frame):
        ## Path
        # Find current path outline/contour (only every 3rd frame)
        # if frame_count % 3 == 0:
        #     new_path = detect_path(frame)
        #     if new_path is not None:
        #         path = new_path

        ## Ball
        # Find current ball position
        if self.ball_pos is None:    # If ball was not detected during last cycle, search entire video frame
            self.ball_pos = self.detect_blue_ball(frame)
        else:                   # If ball was detected last cycle, search only the area surrounding the most recently recorded ball position
            x_min_offset = min(0, self.ball_pos[0] - self.area_size)
            y_min_offset = min(0, self.ball_pos[1] - self.area_size)
            x_min, x_max = max(0, self.ball_pos[0] - self.area_size), self.ball_pos[0] + self.area_size
            y_min, y_max = max(0, self.ball_pos[1] - self.area_size), self.ball_pos[1] + self.area_size
            new_ball_pos = self.detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
            
            # If a ball was successfully detected near prior ball position, calculates new ball position from relative coordinates
            if new_ball_pos is not None:
                new_ball_pos = (
                    max(0, new_ball_pos[0] + self.ball_pos[0] - self.area_size - x_min_offset), 
                    max(0, new_ball_pos[1] + self.ball_pos[1] - self.area_size - y_min_offset),
                    new_ball_pos[2]
                )
            self.ball_pos = new_ball_pos

        # If ball not found during this cycle, tally a detection failure 
        if self.ball_pos is None:
            self.missed_frames_ball += 1

    def annotate_path(self, frame):
        # Draw path
        if self.path is not None:
            cv.drawContours(frame, self.path, -1, color_map["orange"], 2)

    def annotate_ball(self, frame):
        # Draw ball position and message text
        if self.ball_pos is not None:
            msg, msg_color = "Ball detected", "green"
            draw_circles(frame, [self.ball_pos], BGR_color=color_map["magenta"])
            annotate_point(frame, f'{self.ball_pos[0]},{self.ball_pos[1]}', self.ball_pos, color_map['magenta'])
        else:
            msg, msg_color = "Ball NOT detected", "red"
        draw_text(frame, msg, self.text_tl, color_map[msg_color])


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
        display_performance(frame, d.text_tr, d.text_spacing, start, end, frame_time)

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
