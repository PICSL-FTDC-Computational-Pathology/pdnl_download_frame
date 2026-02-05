
import os
import sys
import argparse
from io import BytesIO

import numpy as np
from PIL import Image
import pandas as pd
from phas.client.api import Client, Task, Slide
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--key')
parser.add_argument('-o', '--output_file', type=str)
parser.add_argument('-p', '--project_id', choices=['cndr', 'dots', 'pdnl'], default='dots')
parser.add_argument('-s', '--specimen_id')
parser.add_argument('-b', '--block_id')
parser.add_argument('-a', '--antibody')
parser.add_argument('--section', default=None)
parser.add_argument('--x', default=None, type=int)
parser.add_argument('--y', default=None, type=int)
parser.add_argument('--w', default=None, type=int)
parser.add_argument('--h', default=None, type=int)
parser.add_argument('--level', default=None, type=int)
args = parser.parse_args()

conn = Client('https://chead.uphs.upenn.edu', args.key, verify=False)

for t in conn.task_listing(args.project_id):
    if t['name'] == 'Browse':

        task = Task(conn, task_id=t['id'])

        manifest = task.slide_manifest(
            specimen=args.specimen_id,
            block=args.block_id,
            stain=args.antibody,
            section=args.section,
        )

        if len(manifest['id']) == 0:
            print('ERROR: Invalid query')
            exit()
        if len(manifest['id']) > 1:
            print('Multiple slides exist | Pick a section and re-run with `--section section_id` argument')
            for x in manifest['id']:
                section = manifest['section'][x]
                name = manifest['slide_name'][x]
                print(f'Section={section} -- Name={name}')
            exit()

        slide_id = manifest['id'][0]

        slide = Slide(task=task, slide_id=slide_id)

        if args.x is None:
            tb_level = np.argmax(slide.level_downsamples)
            sw, sh = slide.level_dimensions[0]
            sctr = (int(sw//2), int(sh//2))

            tb_size = slide.level_dimensions[tb_level]
            img = slide.get_patch(center=sctr, level=tb_level, size=tb_size, tile_size=max(tb_size))

            fig, ax = plt.subplots(1,1)
            ax.imshow(img, extent=(0, sw, sh, 0))
            ax.set_title('Thumbnail')
            plt.show()

        else:
            img = slide.get_patch(
                center=(args.x, args.y),
                level=args.level,
                size=(args.w, args.h)
            )
            img.save(args.output_file)
