from collections import namedtuple
import random


Color = namedtuple('Color', ['r', 'g', 'b'])


# Use Vectors to handle figuring out the stroke directions
class Vector(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if not isinstance(other, Vector):
            raise TypeError("can only add two Vectors.")
        return Vector(self.x + other.x, self.y + other.y)

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def scale(self, n):
        return Vector(self.x * n, self.y * n)


HORIZONTAL, VERTICAL = Vector(1, 0), Vector(0, 1),
RANDOM = 'random'


class Painting(object):
    '''A representation of a masterpiece!'''

    def __init__(self, ref, canvas, strokes):
        self.ref = ref
        self.canvas = canvas
        self.num_strokes = len(strokes)
        self.strokes = strokes

    def __mul__(self, other):
        '''
        Simulate reproduction by randomly selecting strokes from this
        painting and the other.
        '''
        canvas = random.choice([self.canvas, other.canvas])

        strokes = []
        for i in range(self.num_strokes):
            strokes.append(random.choice([self, other]).strokes[i])

        return Painting(self.ref, canvas, strokes)

    @classmethod
    def generate(cls, ref, image, color_generator, canvas, num_strokes):
        '''
        Generate a new random painting!

        Args:
            ref: the ref ID of the image.
            image: the PIL.Image representation of the image file.
            color_generator: a generator with .next() implemented, to give
                a weighted random color.
            canvas: the canvas color.
            num_strokes: how many strokes the painting should have.

        Returns:
            a new Painting with a random set of strokes.
        '''
        strategy = random.choice([HORIZONTAL, VERTICAL, RANDOM])
        rgb = canvas[:3]
        canvas = Color(*rgb)
        brush_size = random.randint(2, 12)
        distance = random.randint(5, 200)
        w, h = image.size

        if strategy == HORIZONTAL:
            num_lines = h // (2 * brush_size)
            strokes_per_line = num_strokes // num_lines
            stroke_length = max(
                (w // strokes_per_line) - 2 * brush_size, 0
            )
        elif strategy == VERTICAL:
            num_lines = w // (2 * brush_size)
            strokes_per_line = num_strokes // num_lines
            stroke_length = max(
                (h // strokes_per_line) - 2 * brush_size, 0
            )
        elif strategy == RANDOM:
            stroke_length = random.randint(0, int((w**2 + h**2)**.5))

        strokes = []
        for i in range(num_strokes):
            if strategy == HORIZONTAL:
                move_x = i % strokes_per_line
                move_y = i // strokes_per_line
                start = Vector(
                    move_x * stroke_length + brush_size * (2 * move_x + 1),
                    brush_size * (2 * move_y + 1)
                )
                end = start + strategy.scale(stroke_length)
            elif strategy == VERTICAL:
                move_x = i // strokes_per_line
                move_y = i % strokes_per_line
                start = Vector(
                    brush_size * (2 * move_x + 1),
                    move_y * stroke_length + brush_size * (2 * move_y + 1)
                )
                end = start + strategy.scale(stroke_length)
            elif strategy == RANDOM:
                start = Vector(random.randint(0, w), random.randint(0, h))
                rand_x = random.randint(start.x - distance, start.x + distance)
                rand_y = random.randint(start.y - distance, start.y + distance)
                end = Vector(min(rand_x, w), min(rand_y, h))

            rgb = color_generator.next()[:3]
            color = Color(*rgb)
            strokes.append(Stroke(color, brush_size, start, end))

        return Painting(ref, canvas, strokes)

    def to_json(self):
        r, g, b = self.canvas

        return {
            'canvasColor': {'r': r, 'g': g, 'b': b},
            'strokes': [stroke.to_json() for stroke in self.strokes]
        }


class Stroke(object):
    '''A representation of a single stroke.'''

    def __init__(self, color, brush_size, start, end):
        self.color = color
        self.brush_size = brush_size
        self.start = start
        self.end = end

    def to_json(self):
        r, g, b = self.color

        return {
            'color': {'r': r, 'g': g, 'b': b},
            'start': {'x': self.start.x, 'y': self.start.y},
            'end': {'x': self.end.x, 'y': self.end.y},
            'brushSize': self.brush_size
        }
