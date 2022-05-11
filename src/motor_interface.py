# interface with ESP-32 maze stepper motor board over Serial

import serial
import yaml
from utils import *

class motor_interface(object):
    esp32 = None
    target = [0, 0]
    angle_string = '<0,0>'
    motor_on = '1'
    motor_off = '0'
    conf_file = config_files['serial']
    # config_file = 'confs/serial.yaml'
    conn_settings = None
    port = None
    baud = None
    timeout = None

    def __init__(self) -> None:
        with open(self.conf_file, 'r') as file:
            self.conn_settings = yaml.safe_load(file)

        self.port = self.conn_settings['port']
        self.baud = self.conn_settings['baudrate']
        self.timeout = self.conn_settings['timeout']

        self.esp32 = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=0.1)

    def send_angle(self):
        self.esp32.write(bytes(self.angle_string, 'utf-8'))

    def motor_enable(self):
        self.esp32.write(bytes(self.motor_on, 'utf-8'))

    def motor_disable(self):
        self.esp32.write(bytes(self.motor_off, 'utf-8'))

    def set_angle(self, new_target):
        self.target = new_target
        self.angle_string = f'<{self.target[0]},{self.target[1]}>'
