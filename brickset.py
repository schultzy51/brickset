#!/usr/bin/env python3

import argparse
import csv
import logging
import os
import simplejson as json
import sys
import webbrowser
import yaml
import zeep
from collections import OrderedDict
from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep

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


class Brickset:
  def __init__(self, api_key, username, password):
    self._client = zeep.Client('https://brickset.com/api/v2.asmx?WSDL')
    self._api_key = api_key
    self._username = username
    self._password = password

  def recent(self, minutes_ago):
    zeep_sets = self._client.service.getRecentlyUpdatedSets(apiKey=self._api_key, minutesAgo=minutes_ago)
    return zeep.helpers.serialize_object(zeep_sets)

  def wanted(self):
    token = self._client.service.login(apiKey=self._api_key, username=self._username, password=self._password)

    if token == 'ERROR: invalid username and/or password':
      raise RuntimeError('ERROR: invalid credentials')

    zeep_sets = self._client.service.getSets(**self.sets_params({'userHash': token, 'wanted': 1, 'apiKey': self._api_key, 'pageSize': 80}))
    return zeep.helpers.serialize_object(zeep_sets)

  def themes(self):
    zeep_themes = self._client.service.getThemes(apiKey=self._api_key)
    return zeep.helpers.serialize_object(zeep_themes)

  def subthemes(self, theme):
    zeep_subthemes = self._client.service.getSubthemes(apiKey=self._api_key, theme=theme)
    return zeep.helpers.serialize_object(zeep_subthemes)

  def years(self, theme):
    zeep_years = self._client.service.getYears(apiKey=self._api_key, theme=theme)
    return zeep.helpers.serialize_object(zeep_years)

  def sets(self, theme, page_size, page_number):
    params = self.sets_params({'theme': theme, 'apiKey': self._api_key, 'pageSize': page_size, 'pageNumber': page_number})
    zeep_sets = self._client.service.getSets(**params)
    return zeep.helpers.serialize_object(zeep_sets)

  @staticmethod
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


def get_config(filename='.config.yml', section='default'):
  with open(filename, 'r') as f:
    cfg = yaml.load(f)

  config = cfg['default']
  config.update(cfg[section])

  # TODO: how to handle missing keys?
  return config


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


def recent_custom(sets, minutes_ago_stop=0, open_web=False, unwanted_themes=None):
  if unwanted_themes is None:
    unwanted_themes = []

  datetime_stop = datetime.utcnow() - timedelta(minutes=minutes_ago_stop)

  sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
  sets = list(filter(lambda d: d['year'] > str(datetime.utcnow().year - 1), sets))
  sets = list(filter(lambda d: d['lastUpdated'] < datetime_stop, sets))

  if open_web:
    for rset in sets:
      webbrowser.open_new_tab(rset['bricksetURL'])

  return sets


def set_order_csv(sets, filename='wanted.csv'):
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

    if args.custom:
      sets = recent_custom(sets, args.minutes_ago_stop, args.open_web, config['unwanted_themes'])

    sets.reverse()
    sets = filter_keys(sets, config['output']['recent'])
    items.extend(sets)

  elif args.command == 'wanted':
    sets = brickset.wanted()

    if args.custom:
      sets = wanted_custom(sets)

    sets = filter_keys(sets, config['output']['wanted'])
    items.extend(sets)

  elif args.command == 'themes':
    themes = brickset.themes()
    themes = filter_keys(themes, config['output']['themes'])
    items.extend(themes)

  elif args.command == 'subthemes':
    subthemes = brickset.subthemes(args.theme)
    subthemes = filter_keys(subthemes, config['output']['subthemes'])
    items.extend(subthemes)

  elif args.command == 'years':
    years = brickset.years(args.theme)
    years = filter_keys(years, config['output']['years'])
    items.extend(years)

  elif args.command == 'sets':
    page_number = 1
    page_size = 50

    while True:
      sets = brickset.sets(args.theme, page_size, page_number)
      sets = filter_keys(sets, config['output']['sets'])
      items.extend(sets)

      if len(sets) != page_size:
        break
      else:
        page_number += 1
        sleep(args.delay)

  elif args.command == 'set_order':
    sets = brickset.wanted()
    sets = wanted_custom(sets)
    set_order_csv(sets)
    sets = filter_keys(sets, config['output']['set_order'])

    items.extend(sets)
  else:
    raise RuntimeError('ERROR: Unknown Command')

except Exception as e:
  sys.exit(e)
else:
  print(json.dumps(items, default=json_serial))
