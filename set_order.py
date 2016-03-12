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
CSV_HEADER = ['id',
              'number',
              # 'number variant',
              'name',
              'year',
              'theme',
              # 'theme group',
              'subtheme',
              'pieces',
              'minifigs',
              'released',
              'url',
              'us retail price',
              # 'last updated',
              'us start',
              'us end',
              'uk start',
              'uk end'
             ]
CSV_HEADER_LENGTH = len(CSV_HEADER)


class Config:
  def __init__(self, raw):
    self.api_key = raw.get('api_key', None)
    self.username = raw.get('username', None)
    self.password = raw.get('password', None)


class Set:
  def __init__(self, id, number, number_variant, name, year, theme, theme_group, subtheme, pieces, minifigs, released, url, us_retail_price, last_updated):
    self.id = id
    self.number = number
    self.number_variant = number_variant
    self.name = name
    self.year = year
    self.theme = theme
    self.theme_group = theme_group
    self.subtheme = subtheme
    self.pieces = pieces
    self.minifigs = minifigs
    self.released = released
    self.url = url  # brickset url
    self.us_retail_price = us_retail_price  # us retail price
    self.last_updated = last_updated

  def __str__(self):
    return "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(self.id,
                                                                           self.number,
                                                                           self.number_variant,
                                                                           self.name,
                                                                           self.year,
                                                                           self.theme,
                                                                           self.theme_group,
                                                                           self.subtheme,
                                                                           self.pieces,
                                                                           self.minifigs,
                                                                           self.released,
                                                                           self.url,
                                                                           self.us_retail_price,
                                                                           self.last_updated
                                                                          )

  def to_a(self):
    return [self.id,
            self.number,
            # self.number_variant,
            self.name,
            self.year,
            self.theme,
            # self.theme_group,
            self.subtheme,
            self.pieces,
            self.minifigs,
            self.released,
            self.url,
            self.us_retail_price,
            # self.last_updated
           ]

def get_config(file='.config'):
  with open(file, 'r') as f:
    raw = (yaml.load(f))

  return Config(raw)


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
    'wanted': '1',
    'orderBy': '',
    'pageSize': '50',
    'pageNumber': '1',
    'userName': ''
  }

  response = requests.post(GET_SETS_URL, data)
  text = response.text.encode(response.encoding)
  doc = untangle.parse(text)

  sets = [
    Set(s.setID.cdata.strip(),
        s.number.cdata.strip(),
        s.numberVariant.cdata.strip(),
        s.name.cdata.strip(),
        s.year.cdata.strip(),
        s.theme.cdata.strip(),
        s.themeGroup.cdata.strip(),
        s.subtheme.cdata.strip(),
        s.pieces.cdata.strip(),
        s.minifigs.cdata.strip(),
        s.released.cdata.strip(),
        s.bricksetURL.cdata.strip(),
        s.USRetailPrice.cdata.strip(),
        s.lastUpdated.cdata.strip())
    for s in doc.ArrayOfSets.sets
    ]

  return sets


def clean_date(date):
  date = date.strip()
  if date == 'now':
    cleaned = time.strftime("%Y%m%d")
  else:
    cleaned = time.strftime("%Y%m%d", time.strptime(date, "%d %b %y"))

  return cleaned


def find_dates(tree, location):
  id = ".//dt[text()='{}']".format(location)
  default_dates = [time.strftime("%d %b %y"), time.strftime("%d %b %y")]

  r = tree.xpath(id)
  raw_dates = r[0].getnext().text.split('-') if r else default_dates  # default to today

  dates = [clean_date(d) for d in raw_dates]

  return dates


def get_dates(url):
  # just a little scraping
  page = requests.get(url)
  tree = html.fromstring(page.content)

  us_dates = find_dates(tree, 'United States')
  uk_dates = find_dates(tree, 'United Kingdom')

  return us_dates + uk_dates


config = get_config()
token = get_token(config)
sets = get_sets(config, token)

# quick and dirty printing for now...

values = []

for s in sets:
  print s.to_a()
  values.append(s.to_a() + get_dates(s.url))

us_ordered = sorted(values, key=itemgetter(CSV_HEADER.index('us start')))
uk_ordered = sorted(values, key=itemgetter(CSV_HEADER.index('uk start')))

if os.path.exists(OUTPUT_CSV):
  os.remove(OUTPUT_CSV)

with open(OUTPUT_CSV, 'w') as o:
  w = csv.writer(o, lineterminator=os.linesep)
  w.writerows([
    ['US Order'] + ['' for s in range(CSV_HEADER_LENGTH-1)],
    CSV_HEADER
  ])
  w.writerows(us_ordered)
  w.writerows([
    ['' for s in range(CSV_HEADER_LENGTH)],
    ['UK Order'] + ['' for s in range(CSV_HEADER_LENGTH-1)],
    CSV_HEADER
  ])
  w.writerows(uk_ordered)
