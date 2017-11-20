#!/usr/bin/env python3

import argparse
import simplejson as json
import sys
from datetime import datetime

from brickset.service import Brickset
from brickset.config import get_config

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('command', help='Command to execute')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-d', '--delay', action='store', dest='delay', type=int, default=2, help='Delay between api calls in seconds')
parser.add_argument('-t', '--theme', action='store', dest='theme', help='Theme')
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')

args = parser.parse_args()


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError('Type not serializable')


def filter_keys(items, wanted_keys):
  return [{k: v for (k, v) in item.items() if k in wanted_keys} for item in items]


items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  if args.command == 'recent':
    sets = brickset.recent(args.minutes_ago)

    sets.reverse()
    sets = filter_keys(sets, config['output']['recent'])
    items.extend(sets)

  elif args.command == 'wanted':
    sets = brickset.wanted()

    sets = filter_keys(sets, config['output']['wanted'])
    items.extend(sets)

  elif args.command == 'owned':
    sets = brickset.owned()

    sets = filter_keys(sets, config['output']['owned'])
    items.extend(sets)

  elif args.command == 'themes':
    themes = brickset.themes()
    themes = filter_keys(themes, config['output']['theme'])
    items.extend(themes)

  elif args.command == 'subthemes':
    subthemes = brickset.subthemes(args.theme)
    subthemes = filter_keys(subthemes, config['output']['subtheme'])
    items.extend(subthemes)

  elif args.command == 'years':
    years = brickset.years(args.theme)
    years = filter_keys(years, config['output']['year'])
    items.extend(years)

  elif args.command == 'sets':
    sets = brickset.sets(theme=args.theme)
    sets = filter_keys(sets, config['output']['set'])
    items.extend(sets)

  else:
    raise RuntimeError('ERROR: Unknown Command')

except Exception as e:
  sys.exit(e)
else:
  print(json.dumps(items, default=json_serial))
