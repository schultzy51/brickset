import logging
import zeep
from time import sleep

logging.basicConfig()
logging.getLogger('zeep').setLevel(logging.ERROR)


class Brickset:
  def __init__(self, api_key, username, password, wsdl_url='https://brickset.com/api/v2.asmx?WSDL'):
    self._client = zeep.Client(wsdl_url)
    self._api_key = api_key
    self._username = username
    self._password = password

  def recent(self, minutes_ago):
    zeep_sets = self._client.service.getRecentlyUpdatedSets(apiKey=self._api_key, minutesAgo=minutes_ago)
    return zeep.helpers.serialize_object(zeep_sets)

  def wanted(self, page_size=50, delay=2):
    return self.sets(page_size=page_size, action='wanted', delay=delay)

  def owned(self, page_size=50, delay=2):
    return self.sets(page_size=page_size, action='owned', delay=delay)

  def themes(self):
    zeep_themes = self._client.service.getThemes(apiKey=self._api_key)
    return zeep.helpers.serialize_object(zeep_themes)

  def subthemes(self, theme):
    zeep_subthemes = self._client.service.getSubthemes(apiKey=self._api_key, theme=theme)
    return zeep.helpers.serialize_object(zeep_subthemes)

  def years(self, theme):
    zeep_years = self._client.service.getYears(apiKey=self._api_key, theme=theme)
    return zeep.helpers.serialize_object(zeep_years)

  def sets_page(self, page_size=50, page_number=1, theme=None, order_by=None, action=None):
    params = {'apiKey': self._api_key, 'pageSize': page_size, 'pageNumber': page_number}

    if action:
      if action not in ['wanted', 'owned']:
        raise RuntimeError('ERROR: invalid action')

      token = self._client.service.login(apiKey=self._api_key, username=self._username, password=self._password)

      if token == 'ERROR: invalid username and/or password':
        raise RuntimeError('ERROR: invalid credentials')

      params.update({'userHash': token, action: '1'})

    if theme:
      params.update({'theme': theme})

    if order_by:
      params.update({'orderBy': order_by})

    zeep_sets = self._client.service.getSets(**self.sets_params(params))
    return zeep.helpers.serialize_object(zeep_sets) or []

  def sets(self, page_size=50, theme=None, order_by=None, action=None, delay=2):
    items = []
    page_number = 1

    while True:
      sets = self.sets_page(page_size=page_size, page_number=page_number, theme=theme, order_by=order_by, action=action)
      items.extend(sets)

      if len(sets) != page_size:
        break
      else:
        page_number += 1
        sleep(delay)

    return items

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
