#!/usr/bin/env python3

from datetime import datetime
from brickset import write_jsonl, parameterize
from brickset.service import Brickset
from brickset.config import get_config
import os
from time import sleep

DELAY = 1
PAGE_SIZE = 100

config = get_config()
brickset = Brickset(config['api_key'], config['username'], config['password'])

errors = []
start = datetime.now()

themes = brickset.themes()

filename = os.path.join('data', 'themes.jsonl')
write_jsonl(filename, themes)

# themes = filter(lambda theme: theme['theme'] == 'Legends of Chima', themes)

for theme in themes:
  print(theme)

  theme_name = theme['theme']
  theme_set_count = theme['setCount']
  theme_subtheme_count = theme['subthemeCount']
  theme_prefix = parameterize(theme_name, sep='_')

  os.makedirs(os.path.join('data', theme_prefix), exist_ok=True)

  sleep(DELAY)

  filename = os.path.join('data', theme_prefix, "{}_years.jsonl".format(theme_prefix))
  years = brickset.years(theme=theme_name)
  write_jsonl(filename, years)

  sleep(DELAY)

  filename = os.path.join('data', theme_prefix, "{}_subthemes.jsonl".format(theme_prefix))
  subthemes = brickset.subthemes(theme=theme_name)
  write_jsonl(filename, subthemes)

  # found_subtheme_count = len(subthemes) - 1  # subtract null subtheme
  # if found_subtheme_count != theme_subtheme_count:
  #   print("'{}' Subtheme count mismatch (expected={}, found={})".format(theme_name, theme_subtheme_count, found_subtheme_count))
  #   errors.extend({'theme': theme_name, 'type': 'subtheme count mismatch', 'expected': theme_subtheme_count, 'found': found_subtheme_count})

  sleep(DELAY)

  filename = os.path.join('data', theme_prefix, "{}_sets.jsonl".format(theme_prefix))
  sets = brickset.sets(theme=theme_name, order_by='YearFrom', page_size=PAGE_SIZE, delay=DELAY)
  write_jsonl(filename, sets)

  found_set_count = len(sets)
  if found_set_count != theme_set_count:
    print("'{}' Set count mismatch (expected={}, found={})".format(theme_name, theme_set_count, found_set_count))
    errors.extend({'theme': theme_name, 'type': 'set count mismatch', 'expected': theme_set_count, 'found': found_set_count})

filename = os.path.join('data', '0000_timestamp.jsonl')
write_jsonl(filename, [{'start': start, 'end': datetime.now()}])

filename = os.path.join('data', 'errors.jsonl')
write_jsonl(filename, errors)
