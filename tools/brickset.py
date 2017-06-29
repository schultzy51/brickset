#!/usr/bin/env python3

import argparse
import logging
import zeep
import simplejson as json
import sys
from configparser import ConfigParser
from datetime import datetime
from time import sleep

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('command', help='Command to execute')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080,
                    help='Recent minutes ago')
parser.add_argument('-d', '--delay', action='store', dest='delay', type=int, default=2,
                    help='Delay between api calls in seconds')
parser.add_argument('-t', '--theme', action='store', dest='theme', help='Theme')
parser.add_argument('-s', '--section', action='store', dest='section', default='DEFAULT', help='Section')

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


if args.command == 'recent':
  zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=api_key, minutesAgo=args.minutes_ago)
  sets = zeep.helpers.serialize_object(zeep_sets)

  for set in sets:
    print(json.dumps(set, default=json_serial))

elif args.command == 'wanted':
  token = client.service.login(apiKey=api_key, username=username, password=password)

  if token == 'ERROR: invalid username and/or password':
    sys.exit('ERROR: invalid credentials')

  zeep_sets = client.service.getSets(**sets_params({'userHash': token, 'wanted': 1}))
  sets = zeep.helpers.serialize_object(zeep_sets)

  for set in sets:
    print(json.dumps(set, default=json_serial))

elif args.command == 'themes':
  zeep_themes = client.service.getThemes(apiKey=api_key)
  themes = zeep.helpers.serialize_object(zeep_themes)

  for theme in themes:
    print(json.dumps(theme, default=json_serial))

elif args.command == 'subthemes':
  zeep_subthemes = client.service.getSubthemes(apiKey=api_key, theme=args.theme)
  subthemes = zeep.helpers.serialize_object(zeep_subthemes)

  for subtheme in subthemes:
    print(json.dumps(subtheme, default=json_serial))

elif args.command == 'years':
  zeep_years = client.service.getYears(apiKey=api_key, theme=args.theme)
  years = zeep.helpers.serialize_object(zeep_years)

  for year in years:
    print(json.dumps(year, default=json_serial))

elif args.command == 'sets':
  page_number = 1
  page_size = 50

  while True:
    params = sets_params({'theme': args.theme, 'pageSize': page_size, 'pageNumber': page_number})
    zeep_sets = client.service.getSets(**params)
    sets = zeep.helpers.serialize_object(zeep_sets)

    for set in sets:
      print(json.dumps(set, default=json_serial))

    if len(sets) != page_size:
      break
    else:
      page_number += 1
      sleep(args.delay)

else:
  sys.exit('ERROR: Unknown Command')
