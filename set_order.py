#!/usr/bin/python

import csv
import os
import requests
import time
import untangle
import yaml
from lxml import html

BASE_URL = 'http://brickset.com'
LOGIN_URL = BASE_URL + '/api/v2.asmx/login'
GET_SETS_URL = BASE_URL + '/api/v2.asmx/getSets'
OUTPUT_CSV = 'output.csv'
CSV_HEADER = [
  'Number',
  'Name',
  'Year',
  'Theme',
  'Pieces',
  'Minifigs',
  'Brickset URL',
  'US Retail Price',
  'Released',
  'US Start Date',
  'US End Date',
  'UK Start Date',
  'UK End Date'
]
CSV_HEADER_LENGTH = len(CSV_HEADER)


class Config:
  @staticmethod
  def from_yaml(file='.config'):
    with open(file, 'r') as f:
      raw = (yaml.load(f))

    return Config(raw)

  def __init__(self, raw):
    self.api_key = raw.get('api_key', None)
    self.username = raw.get('username', None)
    self.password = raw.get('password', None)


class Set:
  def __init__(self,
               id,
               number,
               number_variant=None,
               name=None,
               year=None,
               theme=None,
               theme_group=None,
               subtheme=None,
               pieces=None,
               minifigs=None,
               released=None,
               brickset_url=None,
               us_retail_price=None,
               last_updated=None,
               us_start_date=None,
               us_end_date=None,
               uk_start_date=None,
               uk_end_date=None):
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
    self.brickset_url = brickset_url  # brickset url
    self.us_retail_price = us_retail_price  # us retail price
    self.last_updated = last_updated
    self.us_start_date = us_start_date
    self.us_end_date = us_end_date
    self.uk_start_date = uk_start_date
    self.uk_end_date = uk_end_date

  def is_released(self):
    return 'true' == self.released

  def __str__(self):
    return "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
        self.id,
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
        self.brickset_url,
        self.us_retail_price,
        self.last_updated,
        self.us_start_date,
        self.us_end_date,
        self.uk_start_date,
        self.uk_end_date
    )

  def to_a(self):
    return [
      self.number,
      self.name,
      self.year,
      self.theme,
      self.pieces,
      self.minifigs,
      self.brickset_url,
      self.us_retail_price,
      self.released,
      self.us_start_date,
      self.us_end_date,
      self.uk_start_date,
      self.uk_end_date
    ]


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
  if date != None:
    date = date.strip()

  if date == None or date == '' or date == 'now':
    cleaned = None
  else:
    cleaned = time.strftime("%Y%m%d", time.strptime(date, "%d %b %y"))

  return cleaned


def find_dates(tree, location):
  id = ".//dt[text()='{}']".format(location)

  r = tree.xpath(id)
  raw_dates = r[0].getnext().text.split('-') if r else [None, None]

  # sometimes the dates are missing on partially released sets
  if (len(raw_dates) != 2):
    raw_dates = [None, None]

  dates = [clean_date(d) for d in raw_dates]

  return tuple(dates)


def get_dates_from_url(url):
  # just a little scraping
  page = requests.get(url)
  tree = html.fromstring(page.content)

  (us_start_date, us_end_date) = find_dates(tree, 'United States')
  (uk_start_date, uk_end_date) = find_dates(tree, 'United Kingdom')

  return us_start_date, us_end_date, uk_start_date, uk_end_date


def get_dates(sets):
  for s in sets:
    if s.is_released():
      (s.us_start_date, s.us_end_date, s.uk_start_date, s.uk_end_date) = get_dates_from_url(s.brickset_url)
    print s

  return sets


def us_sort(a, b):
  return custom_sort(a, b, 'us')


def uk_sort(a, b):
  return custom_sort(a, b, 'uk')


def custom_sort(a, b, country='us'):
  if a.is_released() == b.is_released():
    if a.is_released():  # both released
      a_start_date = a.us_start_date if country == 'us' else a.uk_start_date
      b_start_date = b.us_start_date if country == 'us' else b.uk_start_date
      # check for start_date, compare if both exist, None is last
      if a_start_date is None and b_start_date is None:
        return cmp(a.number, b.number)
      elif (a_start_date is not None and b_start_date is not None):
        return cmp(a_start_date, b_start_date)
      elif a_start_date is None:
        return 1
      else:
        return -1
    else:  # neither released
      return cmp(a.number, b.number)
  elif a.is_released():
    return -1
  else:
    return 1


def output_to_csv(sets):
  us_ordered = map(lambda s: s.to_a(), sorted(sets, cmp=us_sort))
  uk_ordered = map(lambda s: s.to_a(), sorted(sets, cmp=uk_sort))

  if os.path.exists(OUTPUT_CSV):
    os.remove(OUTPUT_CSV)

  with open(OUTPUT_CSV, 'w') as o:
    w = csv.writer(o, lineterminator=os.linesep)
    w.writerows([
      ['US Order'] + ['' for s in range(CSV_HEADER_LENGTH - 1)],
      CSV_HEADER
    ])
    w.writerows(us_ordered)
    w.writerows([
      ['' for s in range(CSV_HEADER_LENGTH)],
      ['UK Order'] + ['' for s in range(CSV_HEADER_LENGTH - 1)],
      CSV_HEADER
    ])
    w.writerows(uk_ordered)


config = Config.from_yaml()
token = get_token(config)
sets = get_sets(config, token)
sets = get_dates(sets)
output_to_csv(sets)
