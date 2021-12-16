from collections import OrderedDict
from datetime import datetime
import csv
import jsonlines
import os
import simplejson as json
import re
import requests
import unicodedata


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


def filter_keys(items, wanted_keys):
  return [{k: v for (k, v) in item.items() if k in wanted_keys} for item in items]


def write_jsonl(filename, items):
  with jsonlines.open(filename, mode='w', dumps=json.JSONEncoder(default=json_serial).encode) as writer:
    writer.write_all(items)


def read_jsonl(filename):
  items = []
  with jsonlines.open(filename) as reader:
    for item in reader:
      items.append(item)

  return items


def write_csv(filename, items, header_dict):
  with open(filename, 'w') as f:
    dict_writer = csv.DictWriter(f, fieldnames=header_dict.keys(), extrasaction='ignore', lineterminator=os.linesep)
    dict_writer.writerow(header_dict)
    dict_writer.writerows(items)


def header_dict(item_dict):
  return OrderedDict([(item, item) for item in item_dict.keys()])

# https://coderwall.com/p/nmu4bg/python-parameterize-equivalent-to-rails-parameterize
def parameterize(string_to_clean, sep='-'):
  parameterized_string = unicodedata.normalize('NFKD', string_to_clean).encode('ASCII', 'ignore').decode()
  parameterized_string = re.sub("[^a-zA-Z0-9\-_]+", sep, parameterized_string)

  if sep is not None and sep != '':
    parameterized_string = re.sub('/#{re_sep}{2,}', sep, parameterized_string)
    parameterized_string = re.sub('^#{re_sep}|#{re_sep}$', sep, parameterized_string, re.I)

  return parameterized_string.lower()


def search(set_id, options={}):
  payload = {
    'fromIndex': '0',
    'locale': 'en-US',
    'onlyAlternatives': 'false',
    'prefixText': set_id
  }
  payload.update(options)
  r = requests.get('https://www.lego.com/service/biservice/search', params=payload)

  if r.status_code == 200:
    return json.loads(r.content)
