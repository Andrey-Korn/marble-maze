
# disable pygame blurb
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
from motor_interface import motor_interface
import time

class ps4_controller(object):
    controller = None
    button_data = None
    axis_data = None
    motors = None

    def __init__(self) -> None:
        pygame.init()
        pygame.joystick.init()
        self.controller = pygame.joystick.Joystick(0)
        self.controller.init()

        # set initial angle
        self.axis_data = [0, 0]

        # initialize motor connection
        self.motors = motor_interface()

    def read_joystick(self):
        # read right joystick angles
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 3:
                    self.axis_data[0] = round(event.value, 2)
                if event.axis == 4:
                    self.axis_data[1] = -round(event.value, 2)


    def set_new_target(self):
        self.motors.set_angle_and_send(self.axis_data)

# control maze via ps4 controller
def main():
    ps4 = ps4_controller()

    while True:
        ps4.read_joystick()
        ps4.set_new_target()
        time.sleep(0.002)


if __name__ == "__main__":
    main()
