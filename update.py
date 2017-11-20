#!/usr/bin/env python3

import argparse
import csv
import logging
import os
import simplejson as json
import sys
import webbrowser
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal

from brickset.service import Brickset
from brickset.config import get_config

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('command', help='Command to execute')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-d', '--delay', action='store', dest='delay', type=int, default=2, help='Delay between api calls in seconds')
parser.add_argument('-t', '--theme', action='store', dest='theme', help='Theme')
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')
parser.add_argument('-c', '--custom', action='store_true', dest='custom', help='Custom filtering and ordering')

args = parser.parse_args()


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


def set_order_csv(sets, filename):
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

  total = 0

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

    # running total
    if wset['released'] and wset['USDateAddedToSAH'] and wset['USRetailPrice']:
      total = total + Decimal(wset['USRetailPrice'])
      wset['total'] = total

  with open(filename, 'w') as f:
    dict_writer = csv.DictWriter(f, fieldnames=key_header.keys(), extrasaction='ignore', lineterminator=os.linesep)
    dict_writer.writerow(key_header)
    dict_writer.writerows(sets)


def filter_keys(items, wanted_keys):
  return [{k: v for (k, v) in item.items() if k in wanted_keys} for item in items]


items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  if args.command == 'recent':
    sets = brickset.recent(args.minutes_ago)

    unwanted_themes = config['unwanted_themes']
    if unwanted_themes is None:
      unwanted_themes = []

    datetime_stop = datetime.utcnow() - timedelta(minutes=args.minutes_ago_stop)

    sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
    sets = list(filter(lambda d: d['year'] > str(datetime.utcnow().year - 1), sets))
    sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))

    if args.open_web:
      for rset in sets:
        webbrowser.open_new_tab(rset['bricksetURL'])

    sets.reverse()
    sets = filter_keys(sets, config['output']['recent'])
    items.extend(sets)

  elif args.command == 'set_order':
    sets = brickset.wanted()

    sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
    sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
    sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

    set_order_csv(sets, 'wanted.csv')
    sets = filter_keys(sets, config['output']['set_order'])

    items.extend(sets)

  elif args.command == 'set_order_owned':
    sets = brickset.owned()

    sets = sorted(sets, key=lambda k: (k['year'] is None, k['year']), reverse=False)
    sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)

    set_order_csv(sets, 'owned.csv')
    sets = filter_keys(sets, config['output']['set_order_owned'])

    items.extend(sets)
  else:
    raise RuntimeError('ERROR: Unknown Command')

except Exception as e:
  sys.exit(e)
else:
  print(json.dumps(items, default=json_serial))
