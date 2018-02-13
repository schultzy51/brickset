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
import sys
from urllib.parse import urlparse
from brickset import read_jsonl, write_jsonl, search
from IPython import embed
from time import sleep

filename = os.path.join('lists', 'owned.jsonl')
sets = read_jsonl(filename)

set_ids = [s['number'] for s in sets]
set_ids.sort()

data = []

for id in set_ids:
  sleep(0.5)
  result = search(id)
  if result:
    data.append({'prefixText': id, 'response': result})
  else:
    print("Error searching for set '{}'".format(id))

filename = os.path.join('instructions', 'search.json'.format(id))
write_jsonl(filename, data)

# searches = read_jsonl(filename)

# for search in searches:
#   # os.makedirs(search['prefixText'], exist_ok=True)
#   embed()


# with open('/Users/scott/Downloads/cat3.jpg', 'wb') as f:
#     f.write(r.content)
