#!/usr/bin/env python3

import argparse
import math
import simplejson as json
import sys
import webbrowser
from datetime import datetime, timedelta
from time import sleep

from brickset import filter_keys, json_serial
from brickset.service import Brickset
from brickset.config import get_config
from brickset.slack import Slack

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')
parser.add_argument('-c', '--slack', action='store_true', dest='slack', help='Slack')
parser.add_argument('-e', '--epoch', action='store', dest='epoch', type=int, help='Last checked epoch')
parser.add_argument('-i', '--image-only', action='store_true', dest='image', help='Only sets with an image')

args = parser.parse_args()

items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  if args.epoch:
    diff = datetime.utcnow() - datetime.utcfromtimestamp(args.epoch)
    args.minutes_ago = diff.days * 1440 + math.ceil(diff.seconds / 60)

  sets = brickset.recent(args.minutes_ago) or []

  unwanted_themes = config['unwanted_themes']
  if unwanted_themes is None:
    unwanted_themes = []

  if args.image:
    sets = list(filter(lambda d: d['image'] == True, sets))

  datetime_stop = datetime.utcnow() - timedelta(minutes=args.minutes_ago_stop)

  sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
  sets = list(filter(lambda d: d['year'] > str(datetime.utcnow().year - 1), sets))
  sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))

  sets.reverse()

  if args.open_web:
    total_sets = len(sets)
    print("Found {} sets".format(total_sets))
    for i, rset in enumerate(sets):
      webbrowser.open(rset['bricksetURL'], new=1, autoraise=False)
      if (i + 1) % 10 == 0 and i + 1 < total_sets:
        input("Press Enter to continue...({}/{})".format(i + 1, total_sets))
      else:
        sleep(0.5)

  if args.slack:
    slack = Slack(config['slack_api_token'], config['slack_channel'], config['slack_username'])
    for rset in sets:
      slack.post_set(rset)

  sets = filter_keys(sets, config['output']['recent'])
  items.extend(sets)

except Exception as e:
  sys.exit(e)
else:
  if not args.open_web:
    print(json.dumps(items, default=json_serial))
