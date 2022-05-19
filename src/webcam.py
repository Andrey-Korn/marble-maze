import cv2 as cv
from numpy.lib import utils
from utils import *

class webcam():

	def __init__(self, settings):
		self.settings = settings

		# init camera capture
		self.vid = cv.VideoCapture(self.settings['camera_id'])

		# check if camera can open
		if not self.vid.isOpened():
		    print(f"cannot open camera w/id: {self.settings['camera_id']}")
		    exit()

		# set camera properties
		self.set_camera_settings()


	def set_camera_settings(self):
		# set fullscreen
		self.window_name = self.settings['window_name']
		cv.namedWindow(self.window_name, cv.WND_PROP_FULLSCREEN)
		# cv.setWindowProperty(self.window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)

		# set resolution
		self.frame_width = self.settings['resolution'][0]
		self.frame_height = self.settings['resolution'][1]
		self.vid.set(cv.CAP_PROP_FRAME_WIDTH, self.frame_width)
		self.vid.set(cv.CAP_PROP_FRAME_HEIGHT, self.frame_height)


		# set auto white balance
		# self.vid.set(cv.CAP_PROP_AUTO_WB, 0)

		# set frame rate
		self.fps = self.settings['fps']
		self.vid.set(cv.CAP_PROP_FPS, self.fps)

		# set brightness, 0 default, 0-15 sweetspot
		self.vid.set(cv.CAP_PROP_BRIGHTNESS, self.settings['brightness'])

		# set contrast, 0 default, 10-20 sweetspot
		self.vid.set(cv.CAP_PROP_CONTRAST, self.settings['contrast'])

		# set saturation, 48 default, 0 is practically b/w
		self.vid.set(cv.CAP_PROP_SATURATION, self.settings['saturation'])

		# set hue
		# self.vid.set(cv.CAP_PROP_HUE, 0)


	def print_camera_settings(self):
		# for i in range(64):
			# print(f'ID {i} = {self.vid.get(i)}')
		print(f'capture resolution: {self.frame_width} x {self.frame_height}')
		print(f'frame rate: {self.vid.get(cv.CAP_PROP_FPS)}')
		print(f'brightness: {self.vid.get(cv.CAP_PROP_BRIGHTNESS)}')
		print(f'contrast: {self.vid.get(cv.CAP_PROP_CONTRAST)}')
		print(f'saturation: {self.vid.get(cv.CAP_PROP_SATURATION)}')
		# print(f'hue: {self.vid.get(cv.CAP_PROP_HUE)}')
		# print(f'auto white balance: {self.vid.get(cv.CAP_PROP_AUTO_WB)}')
		# print(f'auto wb temperature: {self.vid.get(cv.CAP_PROP_WB_TEMPERATURE)}')
		print(f'frame count: {self.vid.get(cv.CAP_PROP_FRAME_COUNT)}')

	def read_frame(self):
		return self.vid.read()

	def get_window_name(self):
		return self.window_name


# display screen if webcam.py ran as a standalone script
def main():

	# create a camera object with the given config
	conf = config_files['camera_1080']
	vid_settings = read_yaml(conf)
	camera = webcam(vid_settings)

	while True:
		# grab frame
		ret, frame = camera.read_frame()

		if not ret:
			print('End of video stream, exiting...')
			break

		# display frame
		cv.imshow(camera.window_name, frame)

		if cv.waitKey(1) == ord('q'):
			break

	camera.print_camera_settings()
	camera.vid.release()
	cv.destroyAllWindows()

if __name__ == "__main__":
	main()
