#!/usr/bin/python

import argparse
import logging
import zeep
import ConfigParser
import simplejson as json
import webbrowser
from collections import OrderedDict
from datetime import datetime, timedelta

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
# parser.add_argument('command', help='Command to execute')
# parser.add_argument('-a', '--api-key', action='store', dest='api_key', help='Developer api-key', required=True)
# parser.add_argument('-u', '--username', action='store', dest='username', help='Username')
# parser.add_argument('-p', '--password', action='store', dest='password', help='Password')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-s', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0,
                    help='Recent minutes ago stop')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')

args = parser.parse_args()

config = ConfigParser.ConfigParser()
config.read('.config')
wanted = dict(config.items('wanted_account'))

username = wanted['username']
password = wanted['password']
api_key = wanted['api_key']

client = zeep.Client('https://brickset.com/api/v2.asmx?WSDL')


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=api_key, minutesAgo=args.minutes_ago)
sets = zeep.helpers.serialize_object(zeep_sets)

unwanted_themes = [
  'Books',
  'Collectable Minifigures',
  'DC Super Hero Girls',
  'Duplo',
  'Elves',
  'Friends',
  'Gear',
  'Juniors',
  'Nexo Knights',
  'Ninjago',
  'The LEGO Ninjago Movie'
]

key_header = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('USRetailPrice', 'US Retail Price'),
  ('lastUpdated', 'Last Updated')
])

datetime_stop = datetime.now() - timedelta(minutes=args.minutes_ago_stop)

sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))
sets = list(filter(lambda d: d['year'] > str(datetime.now().year - 1), sets))
sets.reverse()

for rset in sets:
  if args.open_web:
    webbrowser.open_new_tab(rset['bricksetURL'])

  # remove unwanted keys
  unwanted_keys = set(rset.keys()) - set(key_header.keys())
  for k in unwanted_keys:
    del rset[k]

  # remove whitespace
  for k in rset.keys():
    if isinstance(rset[k], str):
      rset[k] = rset[k].strip()

  # shorten the datetime
  if rset['lastUpdated']:
    rset['lastUpdated'] = rset['lastUpdated'].strftime("%Y-%m-%d %H:%M:%S")

  print(json.dumps(rset, default=json_serial))
