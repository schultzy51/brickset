#!/usr/bin/env python3

import os
import sys
from collections import OrderedDict
from decimal import Decimal

from brickset import write_jsonl, write_csv
from brickset.service import Brickset
from brickset.config import get_config

# TODO: load key_header from config
WANTED_KEY_HEADER = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('minifigs', 'Minifigs'),
  ('USRetailPrice', 'US Retail Price'),
  ('total', 'Running Total'),
  ('released', 'Released'),
  ('USDateAddedToSAH', 'US Start Date'),
  ('USDateRemovedFromSAH', 'US End Date'),
  ('lastUpdated', 'Last Updated')
])

# TODO: load key_header from config
OWNED_KEY_HEADER = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('minifigs', 'Minifigs'),
  ('USRetailPrice', 'US Retail Price'),
  ('USDateAddedToSAH', 'US Start Date'),
])


def clean(sets):
  # clean up the data
  for wset in sets:
    # remove whitespace
    for k in wset.keys():
      if isinstance(wset[k], str):
        wset[k] = wset[k].strip()

    # shorten the datetime
    if wset['lastUpdated']:
      wset['lastUpdated'] = wset['lastUpdated'].strftime("%Y-%m-%d %H:%M:%S")


def running_total(sets):
  total = 0

  for wset in sets:
    # running total
    if wset['released'] and wset['USDateAddedToSAH'] and wset['USRetailPrice']:
      total = total + Decimal(wset['USRetailPrice'])
      wset['total'] = total


def save_wanted(sets):
  # sort
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

  # save as jsonl
  write_jsonl(os.path.join('lists', 'wanted.jsonl'), sets)

  # prepare data for csv
  clean(sets)
  running_total(sets)

  # save to csv
  write_csv(os.path.join('lists', 'wanted.csv'), sets, WANTED_KEY_HEADER)
  write_csv(os.path.join('lists', 'wanted_released.csv'), filter(lambda k: k['released'], sets), WANTED_KEY_HEADER)


def save_owned(sets):
  # sort
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['year'] is None, k['year']), reverse=False)

  # save as jsonl
  write_jsonl(os.path.join('lists', 'owned.jsonl'), sets)

  # prepare data for csv
  clean(sets)

  # save to csv
  write_csv(os.path.join('lists', 'owned.csv'), sets, OWNED_KEY_HEADER)


try:
  # setup
  config = get_config(section='wanted')
  brickset = Brickset(config['api_key'], config['username'], config['password'])
  os.makedirs('lists', exist_ok=True)

  # get and save wanted sets
  save_wanted(brickset.wanted(page_size=100, delay=1))

  # get and save owned sets
  save_owned(brickset.owned(page_size=100, delay=1))

except Exception as e:
  sys.exit(e)
