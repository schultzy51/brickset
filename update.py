#!/usr/bin/env python3

import csv
import os
import sys
from collections import OrderedDict
from decimal import Decimal

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


def set_order_csv(sets, filename, header_hash):
  with open(filename, 'w') as f:
    dict_writer = csv.DictWriter(f, fieldnames=header_hash.keys(), extrasaction='ignore', lineterminator=os.linesep)
    dict_writer.writerow(key_header)
    dict_writer.writerows(sets)


items = []

try:
  config = get_config(section='wanted')
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  sets = brickset.wanted()

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

  clean(sets)
  running_total(sets)
  set_order_csv(sets, 'wanted.csv', key_header)

  sets = brickset.owned()

  sets = sorted(sets, key=lambda k: (k['year'] is None, k['year']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)

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

  clean(sets)
  set_order_csv(sets, 'owned.csv', key_header)

except Exception as e:
  sys.exit(e)
