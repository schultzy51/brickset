#!/usr/bin/env python3

import os
import sys
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

from brickset import write_jsonl, write_csv
from brickset.service_v2 import Brickset
from brickset.config import get_config

# TODO: load key_header from config
WANTED_KEY_HEADER = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('minifigs', 'Minifigs'),
  ('retailPrice', 'US Retail Price'), # missing
  ('total', 'Running Total'),
  ('released', 'Released'),
  ('dateFirstAvailable', 'US Start Date'), # missing
  ('dateLastAvailable', 'US End Date') # mising
])

# TODO: load key_header from config
OWNED_KEY_HEADER = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('minifigs', 'Minifigs'),
  ('retailPrice', 'US Retail Price'), # missing
  ('dateFirstAvailable', 'US Start Date'), # missing
])


# {
# 'setID': 28131,
# 'number': '2432',
# 'numberVariant': 1,
# 'name': "Big Chief's Camp",
# 'year': 1998,
# 'theme': 'Duplo',
# 'themeGroup': 'Pre-school',
# 'category': 'Normal',
# 'released': True,
# 'pieces': 18,
# 'minifigs': 3,
# 'image': {'thumbnailURL': 'https://images.brickset.com/sets/small/2432-1.jpg',
# 'imageURL': 'https://images.brickset.com/sets/images/2432-1.jpg'},
# 'bricksetURL': 'https://brickset.com/sets/2432-1',
# 'collection': {},
# 'collections': {'ownedBy': 12, 'wantedBy': 13},
# 'LEGOCom':
#   {
#   'US':
#     {'retailPrice': 399.99, 'dateFirstAvailable': '2020-09-01T00:00:00Z', 'dateLastAvailable': '2020-09-25T00:00:00Z'},
#   'UK':
#     {'retailPrice': 369.99, 'dateFirstAvailable': '2020-09-01T00:00:00Z'},
#   'CA':
#     {'retailPrice': 499.99, 'dateFirstAvailable': '2020-09-01T00:00:00Z', 'dateLastAvailable': '2020-09-25T00:00:00Z'},
#   'DE':
#     {'retailPrice': 389.91, 'dateFirstAvailable': '2020-09-02T00:00:00Z'}
#   },
# 'rating': 0.0,
# 'reviewCount': 0,
# 'packagingType': 'Box',
# 'availability': '{Not specified}',
# 'instructionsCount': 0,
# 'additionalImageCount': 0,
# 'ageRange': {},
# 'dimensions': {},
# 'barcode': {},
# 'extendedData': {},
# 'lastUpdated': '2020-09-27T08:51:09.82Z'
# }

def clean(sets):
  # clean up the data
  for wset in sets:
    # remove whitespace
    for k in wset.keys():
      if isinstance(wset[k], str):
        wset[k] = wset[k].strip()


def running_total(sets):
  total = 0

  for wset in sets:
    # running total
    if wset['released'] and 'dateFirstAvailable' in wset and 'retailPrice' in wset:
      total = total + Decimal(wset['retailPrice'])
      wset['total'] = round(total, 2)


def save_wanted(sets):
  # merge legocom us values to root
  sets = merge_legocom_us(sets)

  # sort
  sets = sorted(sets, key=lambda k: (k.get('number', None) is None, k.get('number', None)), reverse=False)
  sets = sorted(sets, key=lambda k: (k.get('dateFirstAvailable', None) is None, k.get('dateFirstAvailable', None)), reverse=False)
  sets = sorted(sets, key=lambda k: (k.get('released', None) is None, k.get('released', None)), reverse=True)

  # save as jsonl
  write_jsonl(os.path.join('lists', 'wanted.jsonl'), sets)

  # prepare data for csv
  clean(sets)
  running_total(sets)

  # save to csv
  write_csv(os.path.join('lists', 'wanted.csv'), sets, WANTED_KEY_HEADER)
  write_csv(os.path.join('lists', 'wanted_released.csv'), filter(lambda k: k.get('dateFirstAvailable', None), sets), WANTED_KEY_HEADER)


def save_owned(sets):
  # merge legocom us values to root
  sets = merge_legocom_us(sets)

  # sort
  sets = sorted(sets, key=lambda k: (k.get('number', None) is None, k.get('number', None)), reverse=False)
  sets = sorted(sets, key=lambda k: (k.get('dateFirstAvailable', None) is None, k.get('dateFirstAvailable', None)), reverse=False)
  sets = sorted(sets, key=lambda k: (k.get('year', None) is None, k.get('year', None)), reverse=False)

  # save as jsonl
  write_jsonl(os.path.join('lists', 'owned.jsonl'), sets)

  # prepare data for csv
  clean(sets)

  # save to csv
  write_csv(os.path.join('lists', 'owned.csv'), sets, OWNED_KEY_HEADER)


def merge_legocom_us(sets):
  today = datetime.today().strftime('%Y-%m-%d')

  for set in sets:
    if 'LEGOCom' in set and 'US' in set['LEGOCom']:
      tmp = set['LEGOCom']['US']
      if 'dateFirstAvailable' in tmp:
        tmp['dateFirstAvailable'] = format_date(tmp['dateFirstAvailable'])
      if 'dateLastAvailable' in tmp:
        tmp['dateLastAvailable'] = format_date(tmp['dateLastAvailable'])

        if tmp['dateLastAvailable'] == today:
          del tmp['dateLastAvailable']

      set.update(tmp)

  return sets


def format_date(date):
  return datetime.fromisoformat(date.replace('Z', '+00:00')).strftime('%Y-%m-%d')

try:
  # setup
  config = get_config(section='wanted_api3')
  brickset = Brickset(config['api_key'], config['username'], config['password'])
  os.makedirs('lists', exist_ok=True)

  print(brickset.get_key_usage_stats())

  # get and save wanted sets
  save_wanted(brickset.wanted(page_size=250, delay=1))

  # get and save owned sets
  save_owned(brickset.owned(page_size=250, delay=1))

except Exception as e:
  import code; code.interact(local=dict(globals(), **locals()))
  sys.exit(e)
