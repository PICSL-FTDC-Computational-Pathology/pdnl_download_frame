
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
parser.add_argument('--slide_number', default=None, type=int)
parser.add_argument('--resolution', type=float, required=True)
parser.add_argument('--dry', action='store_true')
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
            print('*******> ERROR: Invalid query')
            exit()
            
        if args.slide_number is None:
            slide_num = 0
            if len(manifest['id']) > 1:
                print('Multiple slides exist | Pick a section and re-run with `--section section_id` argument')                
                for x in manifest['id']:
                    section = manifest['section'][x]
                    name = manifest['slide_name'][x]
                    print(f'Section={section} -- Name={name}')
                exit()
        else:
            slide_num = args.slide_number
            
        slide_id = manifest['id'][slide_num]

        slide = Slide(task=task, slide_id=slide_id)

        spacing = slide.spacing[0]
        level_downsamples = np.array(slide.level_downsamples)
        level_spacing = spacing * level_downsamples
        level_spacing[level_spacing > args.resolution] = 0
        level = np.argmax(level_spacing)
        spacing = np.max(level_spacing)

        # get the center of the slide
        sw, sh = slide.level_dimensions[0]
        sctr = (int(sw//2), int(sh//2))

        # amount of data to load
        tb_size = np.array(slide.level_dimensions[level])

        # size to downsample to after loading
        ds = spacing / args.resolution
        out_size = np.rint(tb_size * ds).astype(int)

        print(f'Loading image of size: {tb_size} ...')
        print(f'Then downsampling to {out_size} ...', flush=True)

        if args.dry:
            continue
        
        img = slide.get_patch(center=sctr, level=level, size=tb_size)
        out_img = img.resize(out_size)
        if args.output_file is None:
            name = manifest['slide_name'][0]+'.png'
        else:
            name = args.output_file
        out_img.save(name)
