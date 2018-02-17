#!/usr/bin/env python3

from brickset import read_jsonl, write_csv, header_dict
import os

# check for data directory
if not os.path.exists('data'):
  raise RuntimeError('data directory missing!')

# check for data/themes.jsonl
themes_file = os.path.join('data', 'themes.jsonl')
if not os.path.exists(themes_file):
  raise RuntimeError('themes.json missing!')

themes = read_jsonl(themes_file)

filename = os.path.join('data', 'themes.csv')
write_csv(filename, themes, header_dict(themes[0]))

themes_directories = [name for name in os.listdir('data') if os.path.isdir(os.path.join('data', name))]

global_sets = []
csv_types = []

# check each theme
for theme_directory in themes_directories:
  for type in ['sets']:  # 'subthemes', 'years'
    # load
    items_file = os.path.join('data', theme_directory, '{}_{}.jsonl'.format(theme_directory, type))
    items = read_jsonl(items_file)

    # write csv
    if type in csv_types:
      filename = os.path.join('data', theme_directory, '{}_{}.csv'.format(theme_directory, type))
      write_csv(filename, items, header_dict(items[0]))

    if type == 'sets':
      global_sets.extend(items)

filename = os.path.join('data', 'sets.csv')
write_csv(filename, global_sets, header_dict(global_sets[0]))
