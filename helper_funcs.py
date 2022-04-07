import cv2 as cv
import numpy as np


# Maps example videos to paths
prefix = "videos"
video_path_map = {
    # Metal ball
    "metal_1":      f'{prefix}/2022-01-23 12-25-15.mp4',
    "metal_2":      f'{prefix}/2022-01-23 12-25-59.mp4',
    "metal_3":      f'{prefix}/2022-01-23 12-26-33.mp4',
    "metal_4":      f'{prefix}/2022-01-23 12-27-05.mp4',

    # Colored ball - orignal
    "blue":         f'{prefix}/2022-03-02 09-51-06.mp4',
    "green":        f'{prefix}/2022-03-02 09-50-40.mp4',
    "red":          f'{prefix}/2022-03-02 09-50-12.mp4',

    # Colored ball - higher brightness
    "blue_bright":  f'{prefix}/2022-03-03 14-06-09.mp4',
    "green_bright": f'{prefix}/2022-03-03 14-05-22.mp4',
    "red_bright":   f'{prefix}/2022-03-03 14-04-44.mp4',
}


# Maps color name strings to tuples representing BGR (Blue Green Red) color values
color_map = {
    "white":        (255,   255,    255 ),
    "black":        (0,     0,      0   ),
    "blue":         (255,   0,      0   ),
    "green":        (0,     255,    0   ),
    "red":          (0,     0,      255 ),
    "yellow":       (0,     255,    255 ),
    "cyan":         (255,   255,    0   ),
    "orange":       (0,     128,    255 ),
    "brightorange": (0,     192,    255 ),
    "magenta":      (255,   0,      255 )
}


def draw_text(img: np.ndarray, text:str, position: tuple, BGR_color: tuple) -> None:
    """ Draws text of color BGR_color to img at position """

    new_img = cv.putText(img, text, position, cv.FONT_HERSHEY_SIMPLEX, 2, BGR_color, 3)
    img = new_img


def draw_circles(img: np.ndarray, circles: list, num: int = -1, BGR_color: tuple = (0, 0, 255)) -> None:
    """ Draws output from cv.HoughCircles onto img """

    if num == -1:
        num = len(circles)

    for c in circles[:num]:
        cv.circle(img, (c[0],c[1]), c[2],  BGR_color, 3)   # Draw circle
        cv.circle(img, (c[0],c[1]), 2,     BGR_color, 3)   # Draw dot at circle's center

    return


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
    # eroded = cv.erode(no_green_red, kernel, iterations=1)
    eroded_dilated = erode_and_dilate(no_green_red, 3)

    final_image = eroded_dilated

    circles = cv.HoughCircles(final_image, cv.HOUGH_GRADIENT, 1, 50, param1=30, param2=15, minRadius=3, maxRadius=50)

    if circles is not None:
        circles = np.uint16(np.around(circles))
        ball = circles[0,:][0]
        return (
            ball[0],
            ball[1],
            ball[2]
        )
    else:
        return None


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
