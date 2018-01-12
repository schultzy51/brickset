#!/usr/bin/env python3

import argparse
import simplejson as json
import sys
import webbrowser
from datetime import datetime, timedelta
from time import sleep
from slacker import Slacker

from brickset import filter_keys, json_serial
from brickset.service import Brickset
from brickset.config import get_config

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')
parser.add_argument('-c', '--slack', action='store_true', dest='slack', help='Slack')

args = parser.parse_args()


def post_set(set):
  # TODO: build title (subtheme optional)
  # title = '{} > {} > {}-{}: {}'.format(set['theme'], set['subtheme'], set['number'], set['numberVariant'], set['name'])

  title = '{}'.format(set['theme'])

  if set['subtheme']:
    title += ' > {}'.format(set['subtheme'])

  title += ' > {}-{}'.format(set['number'], set['numberVariant'])

  if set['name']:
    title += ': {}'.format(set['name'])

  fields = []

  if set['year']:
    fields.append({
      "title": "Year",
      "value": set['year'],
      "short": True
    })

  if set['USRetailPrice']:
    fields.append({
      "title": "RRP",
      "value": set['USRetailPrice'],
      "short": True
    })

  if set['pieces']:
    fields.append({
      "title": "Pieces",
      "value": set['pieces'],
      "short": True
    })

  if False:
    fields.append({
      "title": "Last Updated",
      "value": '{}'.format(set['lastUpdated']),
      "short": True
    })

  attachments = [
    {
      "fallback": title,
      # TODO: change color if wanted or owned
      "color": "#36a64f",
      "title": title,
      "title_link": set['bricksetURL'],
      "fields": fields,
      "image_url": set['imageURL'],
      "ts": set['lastUpdated'].timestamp()
    }
  ]

  slack.chat.post_message(channel='#lego-recent', username='brick', as_user=True, unfurl_links=False, attachments=attachments)


items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  sets = brickset.recent(args.minutes_ago) or []

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

  if args.slack:
    slack = Slacker(config['slack_api_token'])
    for rset in sets:
      post_set(rset)

  sets = filter_keys(sets, config['output']['recent'])
  items.extend(sets)

except Exception as e:
  sys.exit(e)
else:
  print(json.dumps(items, default=json_serial))
