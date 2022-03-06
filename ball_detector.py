import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

from helper_funcs import *


video_path = video_path_map["blue_bright"]
cap = cv.VideoCapture(video_path)

while cap.isOpened():
    
    # Get video frame from file
    ret, frame = cap.read()
    if not ret:
        print("Error: video frame not loaded.")
        break

    detect_and_draw_path(frame)

    ball_pos = detect_blue_ball(frame)

    # Draw ball position and message text onto video frame
    if ball_pos is not None:
        msg, msg_color = "Ball detected", "green"
        draw_circles(frame, [ball_pos], BGR_color=color_map["magenta"])
        draw_text(frame, f"Position (X, Y): {ball_pos[0]}, {ball_pos[1]}", (100, 200), color_map["green"])
    else:
        msg, msg_color = "Ball NOT detected", "red"
    draw_text(frame, msg, (100, 100), color_map[msg_color])

    cv.imshow('Frame', frame)
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()