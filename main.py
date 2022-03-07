import cv2 as cv
import numpy as np
# from matplotlib import pyplot as plt

from helper_funcs import *


# Open video feed/file
video_path = video_path_map["blue_bright"]
cap = cv.VideoCapture(video_path)

# Variables for recording detected object state
path, ball_pos = None, None

# For calculating statistics (object detection accuracy, framerate)
frame_count = 0
missed_frames_ball = 0

# Main loop - object detection and labeling for each video frame
while cap.isOpened():

    ### Step 1: Get video frame
    ret, frame = cap.read()
    if not ret:
        print("Error: video frame not loaded.")
        break
    frame_count += 1

    frame = frame[100:1080, 390:1560,:]  # Crop video frame to only desired area


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
    if ball_pos is None and frame_count < 769:
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
    cv.imshow('Frame', frame)
    
    ### Step 5: Check for exit command
    if cv.waitKey(1) == ord('q'):
        break

cap.release()
cv.destroyAllWindows()

# Print statistics to terminal
print(f"Number of frames where ball was missed: {missed_frames_ball}")
print(f"Ball detection rate: {np.around((1 - missed_frames_ball / frame_count), decimals=4) * 100}%")