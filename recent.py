#!/usr/bin/env python3

import argparse
import logging
import zeep
import simplejson as json
import webbrowser
import yaml
from collections import OrderedDict
from datetime import datetime, timedelta

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')

args = parser.parse_args()


def config(config='.config', section='default'):
  with open(config, 'r') as f:
    cfg = yaml.load(f)

  section = cfg[section]
  section.update(cfg['default'])

  api_key = section.get('api_key', 'api_key')
  username = section.get('username', 'username')
  password = section.get('password', 'password')
  unwanted_themes = section.get('unwanted_themes', None)

  return api_key, username, password, unwanted_themes


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


api_key, username, password, unwanted_themes = config()
client = zeep.Client('https://brickset.com/api/v2.asmx?WSDL')
zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=api_key, minutesAgo=args.minutes_ago)
sets = zeep.helpers.serialize_object(zeep_sets)

key_header = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('USRetailPrice', 'US Retail Price'),
  ('lastUpdated', 'Last Updated')
])

if unwanted_themes is None:
  unwanted_themes = []

datetime_stop = datetime.utcnow() - timedelta(minutes=args.minutes_ago_stop)

sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
sets = list(filter(lambda d: d['year'] > str(datetime.utcnow().year - 1), sets))
sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))
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

print(json.dumps(sets, default=json_serial))
