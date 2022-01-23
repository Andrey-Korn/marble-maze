import cv2 as cv
import webcam
import argparse
import time

# specify command line args
parser = argparse.ArgumentParser(description='Monitor or record a webcam feed.')
parser.add_argument('-r', dest='record', 
                    help='record camera feed to file')
parser.add_argument('--config', 
                    help='change camera config file')
args = parser.parse_args()
# print(args)

# default camera config, or one from arg parse
config_file = 'camera_config_1080.yaml'
if args.config is not None:
    config_file = args.config

# create a camera object with the given config
camera = webcam.webcam(config_file)

video_out = None
if args.record is not None:
    # fourcc = cv.VideoWriter_fourcc('m', 'p', '4', 'v')
    # fourcc = cv.VideoWriter_fourcc(*'mp4v')
    fourcc = cv.VideoWriter_fourcc(*'XVID')
    video_out = cv.VideoWriter(args.record, fourcc, camera.fps, (camera.frame_width, camera.frame_height))

start_t = time.time()

while True:
    # grab frame
    ret, frame = camera.vid.read()

    if not ret:
        print('End of video stream, exiting...')
        break

    # display frame
    cv.imshow(camera.window_name, frame)

    # if video_out is not None:
    video_out.write(frame)

    if cv.waitKey(1) == ord('q'):
        break

end_t = time.time()


camera.print_camera_settings()
camera.vid.release()
video_out.release()
cv.destroyAllWindows()
