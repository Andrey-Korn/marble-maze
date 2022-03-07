import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

from helper_funcs import *


video_path = video_path_map["blue_bright"]
cap = cv.VideoCapture(video_path)

path, ball_pos = None, None
while cap.isOpened():
    
    # Get video frame from file
    ret, frame = cap.read()
    if not ret:
        print("Error: video frame not loaded.")
        break

    frame = frame[100:1080, 390:1560,:]

    new_path = detect_and_draw_path(frame)
    if new_path is not None:
        path = new_path

    if ball_pos is None:    # If no ball was detected during last cycle, search entire video frame
        ball_pos = detect_blue_ball(frame)
    else:                   # If a ball was detected last cycle, search only the area surrounding the ball
        x_min_offset = min(0, ball_pos[0] - 100)
        y_min_offset = min(0, ball_pos[1] - 100)
        x_min, x_max = max(0, ball_pos[0] - 100), ball_pos[0] + 100
        y_min, y_max = max(0, ball_pos[1] - 100), ball_pos[1] + 100
        new_ball_pos = detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
        
        # If a ball was successfully detected, calculates new ball position from relative coordinates of position found
        if new_ball_pos is not None:
            new_ball_pos = (
                max(0, new_ball_pos[0] + ball_pos[0] - 100 - x_min_offset), 
                max(0, new_ball_pos[1] + ball_pos[1] - 100 - y_min_offset),
                new_ball_pos[2]
            )
        ball_pos = new_ball_pos

    # Draw path onto video frame
    if path is not None:
        cv.drawContours(frame, path, -1, color_map["orange"], 2)

    # Draw ball position and message text onto video frame
    if ball_pos is not None:
        msg, msg_color = "Ball detected", "green"
        # print(ball_pos)
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