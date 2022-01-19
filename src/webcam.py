import cv2 as cv
import yaml

class webcam():

	def __init__(self, config_file, cam_id):
		self.config_file = config_file

		# init camera capture
		self.vid = cv.VideoCapture(cam_id)

		# check if camera can open
		if not self.vid.isOpened():
		    print(f"cannot open camera w/id: {cam_id}")
		    exit()

		# read json and set camera properties
		self.read_yaml()
		self.set_camera_settings()


	# use yaml camera config file to read in all desired camera settings
	def read_yaml(self):
		with open(self.config_file, 'r') as file:
			self.settings = yaml.safe_load(file)

		print(self.settings)
		

	def set_camera_settings(self):
		# set fullscreen
		self.window_name = self.settings['window_name']
		cv.namedWindow(self.window_name, cv.WND_PROP_FULLSCREEN)
		cv.setWindowProperty(self.window_name, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)

		# set resolution
		# self.vid.set(cv.CAP_PROP_FRAME_WIDTH, width)
		self.vid.set(cv.CAP_PROP_FRAME_WIDTH, self.settings['resolution'][0])
		# self.vid.set(cv.CAP_PROP_FRAME_HEIGHT, height)
		self.vid.set(cv.CAP_PROP_FRAME_HEIGHT, self.settings['resolution'][1])


	def print_camera_settings(self):
		print(f'capture resolution: {self.vid.get(cv.CAP_PROP_FRAME_WIDTH)} x {self.vid.get(cv.CAP_PROP_FRAME_HEIGHT)}')
