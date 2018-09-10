import bisect
import random


class WeightedRandomColors(object):
    '''
    Adapted from https://eli.thegreenplace.net/2010/01/22/
    weighted-random-generation-in-python/

    Used to create a weight system to get random colors quickly.
    '''

    def __init__(self, color_weights):
        self.totals = []
        self.colors = []
        running_total = 0

        for color, weight in color_weights:
            running_total += weight
            self.totals.append(running_total)
            self.colors.append(color)

    def next(self):
        rnd = random.random() * self.totals[-1]
        ind = bisect.bisect_right(self.totals, rnd)
        return self.colors[ind]

    def __call__(self):
        return self.next()
