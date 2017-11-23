#!/usr/bin/env python3

from brickset import read_jsonl, write_csv
from collections import OrderedDict
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
header_hash = OrderedDict([(item, item) for item in themes[0].keys()])
write_csv(filename, themes, header_hash)

themes_directories = [name for name in os.listdir('data') if os.path.isdir(os.path.join('data', name))]

global_sets = []

# check each theme
for theme_directory in themes_directories:
  # load sets
  sets_file = os.path.join('data', theme_directory, '{}_sets.jsonl'.format(theme_directory))
  sets = read_jsonl(sets_file)

  global_sets.extend(sets)

filename = os.path.join('data', 'sets.csv')
header_hash = OrderedDict([(item, item) for item in global_sets[0].keys()])
write_csv(filename, global_sets, header_hash)
