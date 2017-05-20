#!/usr/bin/python

import argparse
import logging
import zeep
import ConfigParser
import simplejson as json
from datetime import datetime

from collections import OrderedDict

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

parser = argparse.ArgumentParser(description='Brickset Tooling')
# parser.add_argument('command', help='Command to execute')
# parser.add_argument('-a', '--api-key', action='store', dest='api_key', help='Developer api-key', required=True)
# parser.add_argument('-u', '--username', action='store', dest='username', help='Username')
# parser.add_argument('-p', '--password', action='store', dest='password', help='Password')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')

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
  'Duplo',
  'Friends',
  'Nexo Knights'
]

key_header = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  # ('minifigs', 'Minifigs'),
  ('USRetailPrice', 'US Retail Price'),
  # ('bricksetURL', 'Brickset URL'),
  ('lastUpdated', 'Last Updated')
])

sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
sets.reverse()

for set in sets:
  set = {k: set[k] for k in key_header.keys()}
  print(json.dumps(set, default=json_serial))
