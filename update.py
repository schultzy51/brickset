#!/usr/bin/env python3

import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
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
  ('dateLastAvailable', 'US End Date'), # mising
  ('exitDate', 'Exit Date')
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
# 'setID': 50436,
# 'number': '10350',
# 'numberVariant': 1,
# 'name': 'Tudor Corner',
# 'year': 2025,
# 'theme': 'Icons',
# 'themeGroup': 'Model making',
# 'subtheme': 'Modular Buildings Collection',
# 'category': 'Normal',
# 'released': True,
# 'pieces': 3266,
# 'minifigs': 8,
# 'launchDate': '2025-01-01T00:00:00Z',
# 'exitDate': '2028-12-31T00:00:00Z',
# 'image': {
#   'thumbnailURL': 'https://images.brickset.com/sets/small/10350-1.jpg',
#   'imageURL': 'https://images.brickset.com/sets/images/10350-1.jpg'
# },
# 'bricksetURL': 'https://brickset.com/sets/10350-1',
# 'collection': {
#   'setID': 0,
#   'owned': False,
#   'wanted': True,
#   'qtyOwned': 0,
#   'qtyWanted': 1,
#   'qtyOwnedNew': 0,
#   'qtyOwnedUsed': 0,
#   'wantedPriority': 1,
#   'rating': 0,
#   'notes': '',
#   'flags': []
# },
# 'collections': {'ownedBy': 9811, 'wantedBy': 4473},
# 'LEGOCom':
#   {
#   US':
#     { 'retailPrice': 229.99, 'dateFirstAvailable': '2024-12-04T00:00:00Z'},
#   'UK':
#     {'retailPrice': 199.99, 'dateFirstAvailable': '2024-12-04T00:00:00Z'},
#   'CA':
#     {'retailPrice': 299.99, 'dateFirstAvailable': '2024-12-04T00:00:00Z'},
#   'DE':
#     {'retailPrice': 229.99, 'dateFirstAvailable': '2024-12-04T00:00:00Z'}
#   },
# 'rating': 4.4,
# 'ratingCount': 284,
# 'reviewCount': 3,
# 'packagingType': 'Box',
# 'availability': 'LEGO exclusive',
# 'instructionsCount': 7,
# 'additionalImageCount': 15,
# 'ageRange': {'min': 18},
# 'dimensions': {'height': 37.8, 'width': 55.5, 'depth': 13.2, 'weight': 3.554},
# 'modelDimensions': {'dimension1': 31.0, 'dimension2': 26.0, 'dimension3': 25.0},
# 'barcode': {'EAN': '5702017813219', 'UPC': '673419403900'},
# 'itemNumber': {'NA': '6526667', 'EU': '6526662'},
# 'extendedData': {},
# 'lastUpdated': '2025-01-07T22:43:43.763Z'
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
  today = datetime.now(timezone.utc)
  today_string = today.strftime('%Y-%m-%d')

  for set in sets:
    if 'exitDate' in set:
      exit_date = datetime.fromisoformat(set['exitDate'].replace('Z', '+00:00'))

      try:
        one_year_out = today.replace(year=today.year + 1)
      except ValueError:
        # today is Feb 29
        one_year_out = today.replace(year=today.year + 1, day=28)

      if exit_date > one_year_out:
        del set['exitDate']
      else:
        set['exitDate'] = exit_date.strftime('%Y-%m-%d')


    if 'LEGOCom' in set and 'US' in set['LEGOCom']:
      tmp = set['LEGOCom']['US']
      if 'dateFirstAvailable' in tmp:
        tmp['dateFirstAvailable'] = format_date(tmp['dateFirstAvailable'])
      if 'dateLastAvailable' in tmp:
        tmp['dateLastAvailable'] = format_date(tmp['dateLastAvailable'])

        if tmp['dateLastAvailable'] == today_string:
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
