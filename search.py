#!/usr/bin/python

import csv
import os
import requests
import time
import untangle
import yaml
from lxml import html
from operator import itemgetter

BASE_URL = 'http://brickset.com'
LOGIN_URL = BASE_URL + '/api/v2.asmx/login'
GET_SETS_URL = BASE_URL + '/api/v2.asmx/getSets'
OUTPUT_CSV = 'output.csv'


class Config:
  def __init__(self, raw):
    self.api_key = raw.get('api_key', None)
    self.username = raw.get('username', None)
    self.password = raw.get('password', None)


class Set:
  def __init__(self, id, number, number_variant, name, year, theme, subtheme, pieces, image_url, url, released, price):
    self.id = id
    self.number = number
    self.number_variant = number_variant
    self.name = name
    self.year = year
    self.theme = theme
    self.subtheme = subtheme
    self.pieces = pieces
    self.image_url = image_url
    self.url = url  # brickset url
    self.released = released
    self.price = price  # us retail price

def get_config(file='.config'):
  with open(file, 'r') as f:
    raw = (yaml.load(f))

  return Config(raw)

def image_url(set, image):
  image_url = None

  if image == 'true':
    image_url = set.imageURL.cdata.strip()

  return image_url

def get_token(config):
  data = {
    'apiKey': config.api_key,
    'username': config.username,
    'password': config.password
  }

  response = requests.post(LOGIN_URL, data)
  text = response.text.encode(response.encoding)
  doc = untangle.parse(text)

  return doc.string.cdata


def get_sets(config, token):
  data = {
    'apiKey': config.api_key,
    'userHash': token,
    'query': '',
    'theme': '',
    'subtheme': '',
    'setNumber': '',
    'year': '',
    'owned': '',
    'wanted': '',
    'orderBy': 'PiecesDESC',
    'pageSize': '50',
    'pageNumber': '1',
    'userName': config.username
  }

  response = requests.post(GET_SETS_URL, data)
  text = response.text.encode(response.encoding)
  doc = untangle.parse(text)

  print text

  sets = [
    Set(s.setID.cdata.strip(),
        s.number.cdata.strip(),
        s.numberVariant.cdata.strip(),
        s.name.cdata.strip(),
        s.year.cdata.strip(),
        s.theme.cdata.strip(),
        s.subtheme.cdata.strip(),
        s.pieces.cdata.strip(),
        image_url(s, s.image.cdata.strip()),
        s.bricksetURL.cdata.strip(),
        s.released.cdata.strip(),
        s.USRetailPrice.cdata.strip())
    for s in doc.ArrayOfSets.sets
    ]

  return sets


config = get_config()
token = get_token(config)
sets = get_sets(config, token)

# quick and dirty printing for now...

values = []

for s in sets:
  print "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
    s.id,
    s.number,
    s.number_variant,
    s.name,
    s.year,
    s.theme,
    s.subtheme,
    s.pieces,
    s.image_url,
    s.url,
    s.released,
    s.price
    )
