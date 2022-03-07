import cv2 as cv
import numpy as np
# from matplotlib import pyplot as plt

from helper_funcs import *


# Open video feed/file
video_path = video_path_map["blue_bright"]
cap = cv.VideoCapture(video_path)

path, ball_pos = None, None

frame_count = 0
missed_frames_ball = -1
while cap.isOpened():

    # Get video frame from file
    ret, frame = cap.read()
    if not ret:
        print("Error: video frame not loaded.")
        break

    # Crop video frame to only desired area (increases speed and accuracy)
    frame = frame[100:1080, 390:1560,:]

    # Find current path outline (only every 3rd frame)
    if frame_count % 3 == 0:
        new_path = detect_path(frame)
        if new_path is not None:
            path = new_path

    # Find new ball position
    if ball_pos is None:    # If ball was not detected during last cycle, search entire video frame
        ball_pos = detect_blue_ball(frame)

        if frame_count < 769:
            missed_frames_ball += 1

    else:                   # If ball was detected last cycle, search only the area surrounding the most recent ball position
        area_size = 100
        x_min_offset = min(0, ball_pos[0] - area_size)
        y_min_offset = min(0, ball_pos[1] - area_size)
        x_min, x_max = max(0, ball_pos[0] - area_size), ball_pos[0] + area_size
        y_min, y_max = max(0, ball_pos[1] - area_size), ball_pos[1] + area_size
        new_ball_pos = detect_blue_ball(frame[y_min:y_max, x_min:x_max, :])
        
        # If a ball was successfully detected, calculates new ball position from relative coordinates of position found
        if new_ball_pos is not None:
            new_ball_pos = (
                max(0, new_ball_pos[0] + ball_pos[0] - area_size - x_min_offset), 
                max(0, new_ball_pos[1] + ball_pos[1] - area_size - y_min_offset),
                new_ball_pos[2]
            )
        ball_pos = new_ball_pos

    # Draw path onto video frame
    if path is not None:
        cv.drawContours(frame, path, -1, color_map["orange"], 2)

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

    frame_count += 1

cap.release()
cv.destroyAllWindows()

print(f"Number of frames where ball was missed: {missed_frames_ball}")
print(f"Ball detection rate: {(1 - missed_frames_ball / frame_count) * 100}%")