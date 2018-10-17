from collections import Counter, namedtuple
from math import ceil
from operator import itemgetter
import random

from painting import Painting
from weighted_random import WeightedRandomColors


ScoredPainting = namedtuple('ScoredPainting', ['score', 'painting', 'gen_id'])

# Constants
SPAN, RANDOM, SURVIVORS = 'span', 'random', 'survivors'


class GeneticsError(Exception):
    pass


class BreedError(GeneticsError):
    pass


class GeneticPainting(object):
    '''
    Represents genetic painting population parameters.

    Args:
        ref: the gallery reference number for the painting.
        image: the PIL.Image object of the painting.
        num_strokes: how many strokes each painting can have.
        pop_size: the population size (how many paintings to create)
        mutation_chance: the chance an organism has to mutate.
        fit_percentage: percentage of top paintings to "naturally" select
        lucky_percentage: percentage of non-top paintings that get lucky
    '''

    def __init__(
        self, ref, image, num_strokes, pop_size, mutation_chance,
        fit_percentage, lucky_percentage
    ):
        self.ref = ref
        self.image = image
        self.num_strokes = num_strokes
        self.pop_size = pop_size
        self.mutation_chance = mutation_chance
        self.fit_percentage = fit_percentage
        self.lucky_few = int(ceil(pop_size * lucky_percentage))

        self.generation = 0
        self.num_children = int(
            pop_size // (pop_size * fit_percentage + self.lucky_few)
        )

        # Calculate some color weights for smarter randomization
        image_data = list(image.getdata())
        color_weights = [
            (color, count)
            for color, count in Counter(image_data).items()
            if count > 1
        ]
        color_weights = sorted(color_weights, key=itemgetter(1))

        self.canvas = color_weights[-1][0]  # use most common color
        self.weights = WeightedRandomColors(color_weights)

        self.population = self.create_population()

    def _generate_painting(self):
        return Painting.generate(
            self.ref, self.image, self.weights, self.canvas, self.num_strokes,
        )

    def create_population(self):
        '''
        Creates a random Painting population of the given size.

        Returns:
            a copy of the list of Paintings generated for this world.
        '''
        self.population = [
            self._generate_painting()
            for i in range(self.pop_size)
        ]

        return list(self.population)

    def score_population(self, score_func):
        '''
        Scores the current population!

        Args:
            score_func: a scoring function that takes in three
                arguments:
                    this GeneticPainting object
                    a generation id
                    and a painting
                and output a score (int or float).

        Returns:
            an array of namedtuples like (score, painting)
        '''
        scored = list()
        for i, painting in enumerate(self.population):
            score = score_func(self, i + 1, painting)
            scored.append(ScoredPainting(score, painting, i + 1))

        return scored

    def cull_the_herd(self, scored_generation, strategy=SURVIVORS):
        '''
        Performs the selection on the supplied, scored generation.

        Args:
            scored_generation: an array of tuples, (score, painting)
            strategy: how to choose the lucky few; either
                genetics.SURVIVORS or genetics.RANDOM. SURVIVORS will
                choose from the survivors not already chosen by score,
                while RANDOM will generate new, random Paintings to
                intermingle with the winners. Default is SURVIVORS.

        Returns:
            the survivors of this generation, an array of paintings.
        '''
        winners = int(self.pop_size * self.fit_percentage)
        sorted_pop = sorted(scored_generation, key=itemgetter(0))

        survivors = sorted_pop[-winners:]
        if strategy == SURVIVORS:
            additions = random.sample(sorted_pop[:winners], self.lucky_few)
        elif strategy == RANDOM:
            additions = [
                ScoredPainting(0, self._generate_painting(), 0)
                for _ in range(self.lucky_few)
            ]

        survivors.extend(additions)

        return [painting for score, painting, gen_id in survivors]

    def mutate(self):
        '''
        Mutates the current population of paintings, if they're lucky, by
        shuffling the order of their strokes.
        '''
        for painting in self.population:
            if random.random() < self.mutation_chance:
                random.shuffle(painting.strokes)

    def breed(self, breeders, strategy=SPAN):
        '''
        Breeds the given generation, producing a new one!

        Args:
            breeders: an array of paintings to breed. The class of these
                paintings must have __mult__ defined.
            strategy: one of genetics.RANDOM or genetics.SPAN. If RANDOM,
                the paintings will be paired off entirely randomly. If
                SPAN, the paintings will be paired off such that every
                painting breeds. Default is SPAN.

        Returns:
            an array of the next generation.
        '''
        next_generation = list()

        if strategy == RANDOM:
            while len(next_generation) < self.pop_size:
                parent1, parent2 = random.sample(breeders, 2)
                next_generation.append(parent1 * parent2)
        elif strategy == SPAN:
            for i in range(len(breeders) // 2):
                for child in range(self.num_children):
                    parent1 = breeders[i]
                    parent2 = breeders[len(breeders) - (i + 1)]
                    next_generation.append(parent1 * parent2)

            # Handle two cases where the generation might be off a little
            while len(next_generation) < self.pop_size:
                parent1, parent2 = random.sample(breeders, 2)
                next_generation.append(parent1 * parent2)

            next_generation = next_generation[:self.pop_size]
        else:
            raise BreedError(f"Unsupported breeding strategy: {strategy}")

        self.population = next_generation
        self.generation += 1
        return next_generation
