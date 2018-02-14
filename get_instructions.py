#!/usr/bin/env python3

# Parse 'https://www.lego.com/en-us/service/buildinginstructions' for themes and years
# https://www.lego.com//service/biservice/search\?fromIndex\=0\&locale\=en-US\&onlyAlternatives\=false\&prefixText\=10225
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=0&onlyAlternatives=false&theme=10000-20070
# https://www.lego.com//service/biservice/searchbythemeandyear?fromIndex=0&onlyAlternatives=false&theme=10000-20070&year=2004
# https://www.lego.com//service/biservice/searchbylaunchyear?fromIndex=0&onlyAlternatives=false&year=2004
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=0&onlyAlternatives=false&theme=10000-20002
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=10&onlyAlternatives=false&theme=10000-20002
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=20&onlyAlternatives=false&theme=10000-20002

import os
import requests
from wget import filename_from_url
from brickset import read_jsonl, write_jsonl, search
from time import sleep
import urllib

# from urllib.parse import urlparse
from IPython import embed

SEARCH_DELAY = 0.5
DOWNLOAD_DELAY = 0.5

filename = os.path.join('instructions', 'search.json')

if not os.path.isfile(filename):
  filename = os.path.join('lists', 'owned.jsonl')
  sets = read_jsonl(filename)

  set_ids = [s['number'] for s in sets]
  set_ids.sort()

  data = []

  for id in set_ids:
    sleep(SEARCH_DELAY)
    result = search(id)
    if result:
      data.append({'prefixText': id, 'response': result})
    else:
      print("Error searching for set '{}'".format(id))

  write_jsonl(filename, data)

searches = read_jsonl(filename)
total_searches = len(searches)

for i, search in enumerate(searches):
  set_id = search['prefixText']
  print('Set {} ({} / {})'.format(set_id, i + 1, total_searches))
  products = search['response']['products']
  for product in products:
    for instruction in product['buildingInstructions']:
      url = instruction['pdfLocation']

      directory = os.path.join('instructions', 'set_{}'.format(set_id))
      os.makedirs(directory, exist_ok=True)

      detected_filename = filename_from_url(url)
      filename = os.path.join(directory, detected_filename)
      if not os.path.isfile(filename):
        sleep(DOWNLOAD_DELAY)

        # TODO: set user agent
        r = requests.get(url)
        if r.status_code == 200:
          with open(filename, 'wb') as f:
            f.write(r.content)
          # TODO: track failed downloads
          print('  Downloaded {}'.format(filename))
        else:
          print('  Failed To Download {}'.format(url))
