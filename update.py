#!/usr/bin/env python3

import sys
from collections import OrderedDict
from decimal import Decimal

from brickset import write_jsonl, write_csv
from brickset.service import Brickset
from brickset.config import get_config


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
  config = get_config(section='wanted')
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  sets = brickset.wanted(page_size=100, delay=1)

  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

  # TODO: load key_header from config
  key_header = OrderedDict([
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

  write_jsonl('wanted.jsonl', sets)
  clean(sets)
  running_total(sets)
  write_csv('wanted.csv', sets, key_header)

  sets = brickset.owned(page_size=100, delay=1)

  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['year'] is None, k['year']), reverse=False)

  # TODO: load key_header from config
  key_header = OrderedDict([
    ('number', 'Number'),
    ('name', 'Name'),
    ('year', 'Year'),
    ('theme', 'Theme'),
    ('pieces', 'Pieces'),
    ('minifigs', 'Minifigs'),
    ('USRetailPrice', 'US Retail Price'),
    ('USDateAddedToSAH', 'US Start Date'),
  ])

  write_jsonl('owned.jsonl', sets)
  clean(sets)
  write_csv('owned.csv', sets, key_header)

except Exception as e:
  sys.exit(e)
