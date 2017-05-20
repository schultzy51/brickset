#!/usr/bin/python

import csv
import logging
import os
import zeep
import ConfigParser
from datetime import datetime
from collections import OrderedDict

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)

config = ConfigParser.ConfigParser()
config.read('.config')
wanted = dict(config.items('wanted_account'))

username = wanted['username']
password = wanted['password']
api_key = wanted['api_key']

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


token = client.service.login(apiKey=api_key, username=username, password=password)
zeep_sets = client.service.getSets(**sets_params({'userHash': token, 'wanted': 1, 'apiKey': api_key, 'pageSize': 80}))
sets = zeep.helpers.serialize_object(zeep_sets)

key_header = OrderedDict([
  ('number', 'Number'),
  ('name', 'Name'),
  ('year', 'Year'),
  ('theme', 'Theme'),
  ('pieces', 'Pieces'),
  ('minifigs', 'Minifigs'),
  ('USRetailPrice', 'US Retail Price'),
  ('released', 'Released'),
  ('USDateAddedToSAH', 'US Start Date'),
  ('USDateRemovedFromSAH', 'US End Date'),
  ('bricksetURL', 'Brickset URL'),
  ('lastUpdated', 'Last Updated')
])

sets = sorted(sets, key=lambda k: (k['number'] is None, k['number']), reverse=False)
sets = sorted(sets, key=lambda k: (k['USDateAddedToSAH'] is None, k['USDateAddedToSAH']), reverse=False)
sets = sorted(sets, key=lambda k: (k['released'] is None, k['released']), reverse=True)

# clean up the data
for set in sets:
  # remove whitespace
  for k in set.keys():
    if isinstance(set[k], str):
      set[k] = set[k].strip()

  # format the dates to YYYYMMDD
  if set['USDateAddedToSAH']:
    set['USDateAddedToSAH'] = datetime.strptime(set['USDateAddedToSAH'], "%Y-%m-%d").strftime("%Y%m%d")
  if set['USDateRemovedFromSAH']:
    set['USDateRemovedFromSAH'] = datetime.strptime(set['USDateRemovedFromSAH'], "%Y-%m-%d").strftime("%Y%m%d")

  # use true/false rather than True/False
  set['released'] = 'true' if set['released'] else 'false'

with open('wanted.csv', 'w') as f:
  dict_writer = csv.DictWriter(f, fieldnames=key_header.keys(), extrasaction='ignore', lineterminator=os.linesep)
  dict_writer.writerow(key_header)
  dict_writer.writerows(sets)
