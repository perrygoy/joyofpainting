'''
Joy of Painting

Usage:
    jop.py
    jop.py [-h | --help]
    jop.py [-s START -e END --strokes STROKES --popsize POPSIZE --generations GENERATIONS --mutation CHANCE --fit PERCENT --lucky PERCENT]

Options:
    -h --help             Show this message.
    -s --start <start>    Start of the range of gallery IDs to run [default: 0]
    -e --end <end>        End of the range of gallery IDs to run [default: 200]
    --strokes <strokes>   Number of strokes for each painting [default: 500]
    --popsize <size>      Size of the population [default: 1000]
    --generations <size>  Number of generations to go through [default: 100]
    --mutation <chance>   The mutation chance each generation [default: .1]
    --fit <percent>       Percentage (decimal) to select [default: .2]
    --lucky <percent>     Percentage to select by luck [default: .05]
'''

from operator import itemgetter
import os
import shutil

from docopt import docopt

import genetics
import secrets
from jopclient import JoyOfPainting


local_client = JoyOfPainting('local', local=True)
jop_client = JoyOfPainting(secrets.APIKEY)


def score_painting(world, gen_id, painting):
    '''A painting scoring function, to score paintings.'''
    return local_client.paint(
        world.ref, painting, size=world.image.size, gen_id=str(gen_id)
    )


def save_best(ref, gen_id, generation):
    '''
    Saves the best painting for each generation.

    Args:
        ref: the gallery reference ID of the painting.
        gen_id: the generation ID of the reproduction.
        generation: the generation number.
    '''
    created_dir = "images/created/"
    progression_dir = "images/progression/"
    try:
        os.makedirs(f"{progression_dir}{ref}")
    except FileExistsError:
        pass
    finally:
        shutil.copyfile(
            f"{created_dir}{ref}-{gen_id}.png",
            f"{progression_dir}{ref}/{generation}.png"
        )


def cleanup():
    '''Cleans up all the generated images and json files.'''
    created_dir = "images/created/"
    for filename in os.listdir(created_dir):
        if filename.endswith('png'):
            os.remove(f"{created_dir}{filename}")

    json_dir = "images/json/"
    for filename in os.listdir(json_dir):
        if filename.endswith('json'):
            os.remove(f"{json_dir}{filename}")


def happy_little_accidents(
    start=0, end=200, num_strokes=500, pop_size=1000, generations=100,
    mutation_chance=.1, fit_percentage=.02, lucky_percentage=.05
):
    '''
    Attempts to recreate all of the paintings in the gallery using a
    genetic algorithm.

    Args:
        start: the gallery reference ID to begin at. Default is 0.
        end: the gallery reference ID to end at. Default is 200.
        num_strokes: how many strokes each painting can have.
            Default is 500.
        pop_size: how many paintings comprise the population.
            Default is 1000.
        generations: how many generations to go through.
            Default is 100.
        mutation_chance: the chance each organism has to mutate on new
            generations. Default is .1 (10%)
        fit_percentage: percentage of top scoring paintings to select.
            Default is .2 (20%).
        lucky_percentage: percentage of non-top scoring paintings to
            select, if they're lucky enough. Default is .05 (5%).

    Returns:
        A genetics.ScoredPainting named tuple, (score, painting, gen_id)
    '''
    gallery = local_client.gallery()

    pruned_gallery = [
        image
        for image in gallery
        if int(image['id'].split('.')[0]) in range(start, end + 1)
    ]

    print(
        f"Evolving {', '.join(sorted([i['id'] for i in pruned_gallery]))}..."
    )

    best = None
    for image in pruned_gallery:
        ref = image['id']
        image_file = local_client.get_image(ref)

        print(f"Beginning SCIENCE on {ref}!")
        world = genetics.GeneticPainting(
            ref, image_file, num_strokes=num_strokes, pop_size=pop_size,
            mutation_chance=mutation_chance, fit_percentage=fit_percentage,
            lucky_percentage=lucky_percentage,
        )
        world.create_population()

        generation = 0
        scored = world.score_population(score_painting)
        best = max(scored, key=itemgetter(0))
        save_best(ref, best.gen_id, generation)

        for generation in range(1, generations):
            survivors = world.cull_the_herd(
                scored, strategy=genetics.SURVIVORS
            )
            world.breed(survivors)
            world.mutate()

            scored = world.score_population(score_painting)
            best = max(scored, key=itemgetter(0))
            save_best(ref, best.gen_id, generation)
            print(
                f"Generation {world.generation}'s best: "
                f"{best.score} by #{best.gen_id}"
            )

        # Painting submission is now closed.
        # jop_client.paint(ref, best.painting)
        cleanup()
    return best


if __name__ == '__main__':
    args = docopt(__doc__)

    happy_little_accidents(
        start=int(args['--start']),
        end=int(args['--end']),
        num_strokes=int(args['--strokes']),
        pop_size=int(args['--popsize']),
        generations=int(args['--generations']),
        mutation_chance=float(args['--mutation']),
        fit_percentage=float(args['--fit']),
        lucky_percentage=float(args['--lucky']),
    )
