#!/usr/bin/env python3

import argparse
import simplejson as json
import sys
import webbrowser
from datetime import datetime, timedelta
from time import sleep

from brickset import filter_keys, json_serial
from brickset.service import Brickset
from brickset.config import get_config

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')

args = parser.parse_args()

items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

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
      sleep(1)

  sets.reverse()
  sets = filter_keys(sets, config['output']['recent'])
  items.extend(sets)

except Exception as e:
  sys.exit(e)
else:
  print(json.dumps(items, default=json_serial))
