# ball position and target position logger
import json
import numpy as np
import matplotlib.pyplot as plt

class logger():

    log = []
    prefix = 'logs'

    def __init__(self) -> None:
        pass

    def log_new_data(self, ball_pos, target, time):
        entry = [ball_pos, target, time]
        self.log.append(entry)
        
    def load_log(self, log_file):
        f = open(log_file, 'r')
        self.log = json.load(f)
        f.close()

    def write_log(self):
        # print(self.log)
        with open(f'{self.prefix}/log.json', 'w') as file:
            json.dump(self.log, file)

    def graph_log(self):

        # fig, ax = plt.figure(figsize=(18, 6))
        plt.figure(figsize=(18, 6))

        # print(self.log)
        ball = [i[0] for i in self.log]
        ball_x = [i[0] for i in ball]
        ball_y = [i[1] for i in ball]
        target = [i[1] for i in self.log]
        target_x = [i[0] for i in target]
        target_y = [i[0] for i in target]
        time = [i[2] for i in self.log]
        # print(ball)
        # print(target)
        # print(time)

        prefix = 'plots'
        # first plot
        plt.subplot(1, 3, 1)
        plt.plot(ball_x, ball_y, color='blue')
        plt.xlabel("X ball position (px)")
        plt.ylabel("Y ball position (px)")
        plt.gca().invert_yaxis()
        plt.title("X Y ball position")

        # second plot
        plt.subplot(1, 3, 2)
        plt.plot(time, ball_x, color='blue')
        plt.plot(time, target_x, color='red')
        plt.xlabel("time (s)")
        plt.ylabel("X ball position (px)")
        plt.legend(('ball position', 'target position'))
        plt.title("X position over time")

        # third plot
        plt.subplot(1, 3, 3)
        plt.plot(time, ball_y, color='blue')
        plt.plot(time, target_y, color='red')
        plt.gca().invert_yaxis()
        plt.xlabel("time (s)")
        plt.ylabel("Y ball position (px)")
        plt.legend(('ball position', 'target position'))
        plt.title("Y position over time")

        # show and save
        plt.savefig(f'{prefix}/plot.png')
        plt.show()

    def sse(self):
        pass

    def print_stats(self):
        pass


# main graphs the passed in log file with certain settings
def main():
    l = logger()
    log_file = 'logs/log.json'
    l.load_log(log_file)
    l.graph_log()
    l.print_stats()

if __name__ == "__main__":
	main()
