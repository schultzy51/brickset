#!/usr/bin/env python3

# Parse 'https://www.lego.com/en-us/service/buildinginstructions' for themes and years
# Build the following request
# https://www.lego.com//service/biservice/search\?fromIndex\=0\&locale\=en-US\&onlyAlternatives\=false\&prefixText\=10225
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=0&onlyAlternatives=false&theme=10000-20070
# https://www.lego.com//service/biservice/searchbythemeandyear?fromIndex=0&onlyAlternatives=false&theme=10000-20070&year=2004
# https://www.lego.com//service/biservice/searchbylaunchyear?fromIndex=0&onlyAlternatives=false&year=2004

# https://www.lego.com//service/biservice/searchbytheme?fromIndex=0&onlyAlternatives=false&theme=10000-20002
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=10&onlyAlternatives=false&theme=10000-20002
# https://www.lego.com//service/biservice/searchbytheme?fromIndex=20&onlyAlternatives=false&theme=10000-20002


import json
import requests
from urllib.parse import urlparse
from IPython import embed

print('Beginning...')

setId = '42063'
payload = {'fromIndex': '0', 'locale': 'en-US', 'onlyAlternatives': 'false', 'prefixText': setId}
url = 'https://www.lego.com//service/biservice/search'
r = requests.get(url, params=payload)

# with open('/Users/scott/Downloads/cat3.jpg', 'wb') as f:
#     f.write(r.content)

# Retrieve HTTP meta-data
if r.status_code == 200:
  raw = r.content
  data = json.loads(raw)
  count = data['count']
  totalCount = data['totalCount']

  with open("{}_search.json".format(setId), 'w') as file:
    json.dump(data, file)

  if count == 1 and totalCount == 1:
    products = data['products']
    for product in products:
      print('==========================')
      print(product['launchYear'])
      print(product['themeName'])
      print(product['productId'])
      building_instructions = product['buildingInstructions']
      for building_instruction in building_instructions:
        print('++++++++++++++++++++++++++++++')
        print(building_instruction['description'])
        print(building_instruction['downloadSize'])
        print(building_instruction['isAlternative'])
        print(building_instruction['oNum'])
        print(building_instruction['pdfLocation'])

        o = urlparse('http://www.cwi.nl:80/%7Eguido/Python.html')
        embed()

        # r = requests.get(building_instruction['pdfLocation'])

        # with open('/Users/scott/Downloads/cat3.jpg', 'wb') as f:
        #   f.write(r.content)
      # products[0]['buildingInstructions'][0]
  else:
    print('Found multiple sets')
