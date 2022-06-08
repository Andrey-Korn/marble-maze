# ball position and target position logger
import json
import numpy as np
import matplotlib.pyplot as plt
import argparse
from utils import *

class logger():

    log = []
    prefix = 'logs'

    def __init__(self) -> None:
        pass

    def log_new_data(self, ball_pos, target, time, noisy_ball_pos=None):
        entry = [ball_pos, target, time]
        if noisy_ball_pos is not None:
            entry.append(noisy_ball_pos)

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
        target_y = [i[1] for i in target]
        time = [i[2] for i in self.log]
        
        noisy_ball = None
        noisy_ball_x = None
        noisy_ball_y = None
        if len(self.log[0]) > 3:
            noisy_ball = [i[3] for i in self.log]
            noisy_ball_x = [i[0] for i in noisy_ball]
            noisy_ball_y = [i[1] for i in noisy_ball]

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

        if noisy_ball:
            plt.clf()
            plt.figure(figsize=(18, 6))
            
            plt.subplot(1, 3, 1)
            plt.plot(ball_x, ball_y, color='blue')
            plt.plot(noisy_ball_x, noisy_ball_y, color='orange')
            plt.xlabel("X ball position (px)")
            plt.ylabel("Y ball position (px)")
            plt.gca().invert_yaxis()
            plt.legend(('filtered position', 'noisy position'))
            plt.title("X Y ball position")

            plt.subplot(1, 3, 2)
            plt.plot(time, ball_x, color='blue')
            plt.plot(time, target_x, color='red')
            plt.plot(time, noisy_ball_x, color='orange')
            plt.xlabel("time (s)")
            plt.ylabel("X ball position (px)")
            plt.legend(('filtered position', 'target position', 'noisy position'))
            plt.title("X position over time")

            plt.subplot(1, 3, 3)
            plt.plot(time, ball_y, color='blue')
            plt.plot(time, target_y, color='red')
            plt.plot(time, noisy_ball_y, color='orange')
            plt.gca().invert_yaxis()
            plt.xlabel("time (s)")
            plt.ylabel("Y ball position (px)")
            plt.legend(('filtered position', 'target position', 'noisy position'))
            plt.title("Y position over time")

            plt.savefig(f'{prefix}/plot_noisy.png')
            plt.show()


    def sse(self, e):
        error = np.sqrt( abs(e[0])**2 + abs(e[1])**2)**2 
        return error

    def print_stats(self):
        ball = [i[0] for i in self.log]
        ball_x = [i[0] for i in ball]
        ball_y = [i[1] for i in ball]
        target = [i[1] for i in self.log]
        target_x = [i[0] for i in target]
        target_y = [i[0] for i in target]
        time = [i[2] for i in self.log]

        total_error = 0
        for i in range(len(ball)):
            e = ball_error(ball[i], target[i])
            # print(e)
            total_error += self.sse(e)

        print(f'ASE of run: {int(total_error/len(ball))}')
        print(f'Total run time: {time[-1]}')


# main graphs the passed in log file with certain settings
def main():
    desc = 'log file graphing and performance'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-l', '--log', type=str, nargs=1, required=True, help='log file to graph')
    args = parser.parse_args()

    log_file = args.log[0]
    l = logger()
    l.load_log(log_file)
    l.graph_log()
    l.print_stats()

if __name__ == "__main__":
	main()
