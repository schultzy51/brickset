#!/usr/bin/env python3

import argparse
import logging
import zeep
import simplejson as json
import sys
import webbrowser
from configparser import ConfigParser
from datetime import datetime, timedelta
from time import sleep

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('command', help='Command to execute')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-ms', '--minutes-ago-stop', action='store', dest='minutes_ago_stop', type=int, default=0, help='Recent minutes ago stop')
parser.add_argument('-d', '--delay', action='store', dest='delay', type=int, default=2, help='Delay between api calls in seconds')
parser.add_argument('-t', '--theme', action='store', dest='theme', help='Theme')
parser.add_argument('-s', '--section', action='store', dest='section', default='DEFAULT', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')
parser.add_argument('-c', '--custom', action='store_true', dest='custom', help='Custom filtering and ordering')

args = parser.parse_args()

DEFAULT_CONFIG = '.config'

config = ConfigParser()
config.read(DEFAULT_CONFIG)
section = config[args.section]

username = section.get('username', 'username')
password = section.get('password', 'password')
api_key = section.get('api_key', 'api_key')

client = zeep.Client('https://brickset.com/api/v2.asmx?WSDL')


def sets_params(overrides):
  params = {
    'apiKey': '',
    'userHash': '',
    'query': '',
    'theme': '',
    'subtheme': '',
    'setNumber': '',
    'year': '',
    'owned': '',
    'wanted': '',
    'orderBy': 'Number',
    'pageSize': 50,
    'pageNumber': 1,
    'userName': ''
  }
  params.update(overrides)
  return params


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


def wanted_custom(sets):
  sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
  sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

  return sets


def recent_custom(sets, minutes_ago_stop=0, open_web=False):
  # TODO: move this to config
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

  datetime_stop = datetime.utcnow() - timedelta(minutes=minutes_ago_stop)

  sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
  sets = list(filter(lambda d: d['year'] > str(datetime.utcnow().year - 1), sets))
  sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))

  if open_web:
    for rset in sets:
      webbrowser.open_new_tab(rset['bricksetURL'])

  return sets


items = []

if args.command == 'recent':
  zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=api_key, minutesAgo=args.minutes_ago)
  sets = zeep.helpers.serialize_object(zeep_sets)

  if args.custom:
    sets = recent_custom(sets, args.minutes_ago_stop, args.open_web)

  sets.reverse()

  items.extend(sets)

elif args.command == 'wanted':
  token = client.service.login(apiKey=api_key, username=username, password=password)

  if token == 'ERROR: invalid username and/or password':
    sys.exit('ERROR: invalid credentials')

  zeep_sets = client.service.getSets(**sets_params({'userHash': token, 'wanted': 1, 'apiKey': api_key, 'pageSize': 80}))
  sets = zeep.helpers.serialize_object(zeep_sets)

  if args.custom:
    sets = wanted_custom(sets)

  items.extend(sets)

elif args.command == 'themes':
  zeep_themes = client.service.getThemes(apiKey=api_key)
  themes = zeep.helpers.serialize_object(zeep_themes)

  items.extend(themes)

elif args.command == 'subthemes':
  zeep_subthemes = client.service.getSubthemes(apiKey=api_key, theme=args.theme)
  subthemes = zeep.helpers.serialize_object(zeep_subthemes)

  items.extend(subthemes)

elif args.command == 'years':
  zeep_years = client.service.getYears(apiKey=api_key, theme=args.theme)
  years = zeep.helpers.serialize_object(zeep_years)

  items.extend(years)

elif args.command == 'sets':
  page_number = 1
  page_size = 50

  while True:
    params = sets_params({'theme': args.theme, 'apiKey': api_key, 'pageSize': page_size, 'pageNumber': page_number})
    zeep_sets = client.service.getSets(**params)
    sets = zeep.helpers.serialize_object(zeep_sets)

    items.extend(sets)

    if len(sets) != page_size:
      break
    else:
      page_number += 1
      sleep(args.delay)

else:
  sys.exit('ERROR: Unknown Command')

print(json.dumps(items, default=json_serial))
