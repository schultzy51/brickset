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

    # use true/false rather than True/False
    wset['released'] = 'true' if wset['released'] else 'false'


def running_total(sets):
  total = 0

  for wset in sets:
    # running total
    if wset['released'] and wset['USDateAddedToSAH'] and wset['USRetailPrice']:
      total = total + Decimal(wset['USRetailPrice'])
      wset['total'] = total


items = []

try:
  # setup
  config = get_config(section='wanted')
  brickset = Brickset(config['api_key'], config['username'], config['password'])
  os.makedirs('lists', exist_ok=True)

  # get wanted sets
  sets = brickset.wanted(page_size=100, delay=1)

  # sort the wanted sets
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

  # save the wanted sets as jsonl
  filename = os.path.join('lists', 'wanted.jsonl')
  write_jsonl(filename, sets)

  # prepare data for csv
  clean(sets)
  running_total(sets)

  # save the wanted sets to csv
  filename = os.path.join('lists', 'wanted.csv')
  write_csv(filename, sets, WANTED_KEY_HEADER)

  # get the owned sets
  sets = brickset.owned(page_size=100, delay=1)

  # sort the owned sets
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['year'] is None, k['year']), reverse=False)

  # save the owned sets as jsonl
  filename = os.path.join('lists', 'owned.jsonl')
  write_jsonl(filename, sets)

  # prepare data for csv
  clean(sets)

  # save the owned sets to csv
  filename = os.path.join('lists', 'owned.csv')
  write_csv(filename, sets, OWNED_KEY_HEADER)

except Exception as e:
  sys.exit(e)
