from os import error
import cv2 as cv
import numpy as np
from numpy.lib import utils
from webcam import webcam

from utils import *

# bring in file vs webcam choice

def detect_path(img: np.ndarray) -> np.ndarray:
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


def find_maze_corner(src: np.ndarray):
    # search for top left

    # search for top right
    # search for bot left
    # search for bot right
    pass

def perspective_transform(src: np.ndarray):
    pass

def erode_and_dilate(src: np.ndarray, kernel_size: int, iterations: int = 1) -> np.ndarray:
    """ Performs a series of erosions followed by dilations on src image """
    
    erosion_kernel = np.ones((  kernel_size, kernel_size), np.uint8)
    dilation_kernel = (         kernel_size, kernel_size)

    while iterations:
        eroded = cv.erode(src, erosion_kernel, iterations=1)
        src = cv.dilate(eroded, dilation_kernel, iterations=1)
        iterations -= 1

    return src


def detect_blue_ball(src: np.ndarray) -> tuple:
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
    eroded_dilated = erode_and_dilate(no_green_red, 3)
    # eroded_dilated = erode_and_dilate(no_green_red, 1)

    final_image = eroded_dilated

    # uncomment to see ball segmentation
    cv.imshow('ball_mask', final_image)

    # method 2: min enclosing circle
    circles = []
    contours, hierarchy = cv.findContours(eroded_dilated, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
    for c in contours:
        (x,y), r = cv.minEnclosingCircle(c)
        # reject contours that do not meet ball radius
        if r > 15 and r < 30:
            circles.append((x, y, r))
            # print(f'x: {x} y: {y} r: {r}')
            return [int(x), int(y), int(r)]

    return None

    # Method 1: Hough Circles 
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


def main():
    # Open video feed/file
    video_path = video_path_map["blue_bright"]
    # cap = cv.VideoCapture(video_path)
    # cap = cv.VideoCapture()
    conf = config_files['camera_1080']
    camera = webcam(conf)
    settings = read_yaml(conf)
    window_name = settings['window_name']


    # Variables for recording detected object state
    path, ball_pos = None, None

    # For calculating statistics (object detection accuracy, framerate)
    frame_count = 0
    missed_frames_ball = 0

    # Main loop - object detection and labeling for each video frame
    while camera.vid.isOpened():

        ### Step 1: Get video frame
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: video frame not loaded.")
            break
        frame_count += 1

        # Crop video frame to only desired area
        frame = crop_frame(frame, settings['x_frame'], settings['y_frame'])


        ### STEP 2: Detect objects

        ## 2.1: Path
        # Find current path outline/contour (only every 3rd frame)
        if frame_count % 3 == 0:
            new_path = detect_path(frame)
            if new_path is not None:
                path = new_path

        ## 2.2: Ball
        # Find current ball position
        if ball_pos is None:    # If ball was not detected during last cycle, search entire video frame
            ball_pos = detect_blue_ball(frame)
        else:                   # If ball was detected last cycle, search only the area surrounding the most recently recorded ball position
            area_size = 100
            x_min_offset = min(0, ball_pos[0] - area_size)
            y_min_offset = min(0, ball_pos[1] - area_size)
            x_min, x_max = max(0, ball_pos[0] - area_size), ball_pos[0] + area_size
            y_min, y_max = max(0, ball_pos[1] - area_size), ball_pos[1] + area_size
            new_ball_pos = detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
            
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
