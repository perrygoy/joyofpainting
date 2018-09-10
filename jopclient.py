from io import BytesIO
import json
import os
import subprocess

from PIL import Image
from requests import sessions

import secrets


class JoyOfPaintingException(Exception):
    '''For API errors from the Joy of Painting API'''

    def __init__(self, status_code, reason, content):
        self.status_code = status_code
        self.reason = reason
        self.content = content
        super(Exception, self).__init__(content)

    def __repr__(self):
        return "{} {}: {}".format(self.status_code, self.reason, self.content)


class JoyOfPainting(object):
    '''A client to interact with the Joy of Painting API'''

    def __init__(self, key, local=False):
        self.local = local
        self.base_url = secrets.JOP_URL
        self.session = sessions.Session()
        self.session.headers.update({'ApiKey': key})

    def _check_response(self, resp):
        if resp.status_code >= 400:
            raise JoyOfPaintingException(
                resp.status_code, resp.reason, resp.content
            )

    def gallery(self, ref=None):
        '''
        Get information about the images or a specific image in the
        gallery.

        Args:
            ref: the reference ID of a specific image. Default is None.

        Returns:
            an array of all images if ref was not provided, else the
            specific image object.
        '''
        if self.local:
            gallery = [
                {'id': file.split('.')[0]}
                for file in os.listdir('images/reference/')
                if file.endswith('.png')
            ]
        else:
            path = '/gallery/' if ref is None else f'/gallery/{ref}'
            gallery_response = self.session.get(self.base_url + path)
            self._check_response(gallery_response)

            gallery = gallery_response.json()

        return gallery

    def get_image(self, ref):
        '''
        Get a specific image, as a PIL.Image object.

        Args:
            ref: the reference ID of the image.

        Returns:
            PIL.Image object
        '''
        if self.local:
            image_f = f'images/reference/{ref}.png'
        else:
            path = f'/gallery/{ref}'
            image_response = self.session.get(self.base_url + path)
            self._check_response(image_response)

            image_f = BytesIO(image_response.content)

        return Image.open(image_f)

    def paint(self, ref, painting, size=(500, 500), gen_id=''):
        '''
        Submit a painting!

        Args:
            ref: the gallery reference ID
            painting: the painting object to submit. This is an object
                that looks like:
                {
                    'canvasColor': {'r': 0-255, 'g': 0-255, 'b': 0-255},
                    'strokes': [
                        {
                            'start': {'x': #, 'y': #},
                            'end': {'x': #, 'y': #},
                            'brushSize': #,
                            'color': {'r': 0-255, 'g': 0-255, 'b': 0-255}
                        },
                        ...
                    ]
                }
            size: the (x, y) size of the painting. Only needed for local
                painting evaluation. Default is (500, 500)
            gen_id: an optional generation ID for this painting, to save
                many attempts of the same reference. Default is ''.

        Returns:
            the score of the painting.
        '''
        if self.local:
            filename = f"{ref}{f'-{gen_id}' if gen_id else ''}"
            json_filepath = f"images/json/{filename}.json"
            recreation_filepath = f"images/created/{filename}.png"

            with open(json_filepath, 'w+') as jsonfile:
                jsonfile.write(json.dumps(painting.to_json()))

            subprocess.run(
                [
                    "local/create-painting",
                    f"{size[0]}x{size[1]}",
                    json_filepath,
                    recreation_filepath
                ]
            )
            creation = subprocess.run(
                [
                    "local/evaluate-painting",
                    f"images/reference/{ref}.png",
                    recreation_filepath
                ],
                stdout=subprocess.PIPE
            )

            score = float(creation.stdout)
        else:
            path = f'/gallery/{ref}/reproduction'
            paint_response = self.session.post(
                self.base_url + path, json=painting.to_json()
            )
            self._check_response(paint_response)

            score = float(paint_response.json()['similarityScore'])

        return score
