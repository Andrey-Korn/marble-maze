import cv2 as cv
import webcam

config_file = 'camera_config.yaml'
camera_id = 1

camera = webcam.webcam(config_file, camera_id)

while True:
    # grab frame
    ret, frame = camera.vid.read()

    if not ret:
        print('No frame found! Exiting...')
        break

    # display frame
    cv.imshow(camera.window_name, frame)
    if cv.waitKey(1) == ord('q'):
        break


camera.print_camera_settings()
camera.vid.release()
cv.destroyAllWindows()