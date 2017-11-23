#!/usr/bin/env python3

from datetime import datetime
from time import sleep
import os

from brickset import write_jsonl, write_csv, parameterize
from brickset.service import Brickset
from brickset.config import get_config

DELAY = 1
PAGE_SIZE = 100

config = get_config()
brickset = Brickset(config['api_key'], config['username'], config['password'])

errors = []
start = datetime.now()

themes = brickset.themes()

filename = os.path.join('data', 'themes.jsonl')
write_jsonl(filename, themes)

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

  sleep(DELAY)

  filename = os.path.join('data', theme_prefix, "{}_sets.jsonl".format(theme_prefix))
  sets = brickset.sets(theme=theme_name, order_by='YearFrom', page_size=PAGE_SIZE, delay=DELAY)
  write_jsonl(filename, sets)

filename = os.path.join('data', '0000_timestamp.jsonl')
write_jsonl(filename, [{'start': start, 'end': datetime.now()}])

filename = os.path.join('data', 'errors.jsonl')
write_jsonl(filename, errors)
