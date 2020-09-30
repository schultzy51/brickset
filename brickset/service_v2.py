import json
import requests
from time import sleep

class Brickset:
  def  __init__(self, api_key, username, password, base_url='https://brickset.com/api/v3.asmx'):
    self._client = None
    self._api_key = api_key
    self._username = username
    self._password = password
    self._base_url = base_url

  def check_key(self):
    r = requests.get(
      self._base_url + '/checkKey',
      params={
        'apiKey': self._api_key
      }
    )

    # Only the status matters and this will throw an exception if it fails
    self.get_response(r)

    return True

  def login(self):
    r = requests.get(
      self._base_url + '/login',
      params={
        'apiKey': self._api_key,
        'username': self._username,
        'password': self._password
      }
    )

    response = self.get_response(r)

    return response['hash']

  def check_user_hash(self, user_hash):
    r = requests.get(
      self._base_url + '/checkUserHash',
      params={
        'apiKey': self._api_key,
        'userHash': user_hash
      }
    )

    self.get_response(r)

    return True

  def get_key_usage_stats(self):
    r = requests.get(
      self._base_url + '/getKeyUsageStats',
      params={
        'apiKey': self._api_key
      }
    )

    response = self.get_response(r)
    # {'status': 'success', 'matches': 0, 'apiKeyUsage': []}

    return response

  def recent(self, updated_since):
    return self.sets(updated_since=updated_since)

  def wanted(self, page_size=250, delay=2):
    return self.sets(page_size=page_size, action='wanted', delay=delay)

  def owned(self, page_size=250, delay=2):
    return self.sets(page_size=page_size, action='owned', delay=delay)

  def themes(self):
    r = requests.get(
      self._base_url + '/getThemes',
      params={
        'apiKey': self._api_key
      }
    )

    response = self.get_response(r)

    return response

  def subthemes(self, theme):
    r = requests.get(
      self._base_url + '/getSubthemes',
      params={
        'apiKey': self._api_key,
        'Theme': theme
      }
    )

    response = self.get_response(r)

    return response

  def years(self, theme):
    r = requests.get(
      self._base_url + '/getYears',
      params={
        'apiKey': self._api_key,
        'Theme': theme
      }
    )

    response = self.get_response(r)

    return response

  def sets(self, page_size=250, theme=None, order_by=None, action=None, delay=2, updated_since=None):
    items = []
    page_number = 1
    token = ''

    if action is not None:
      token = self.login()

    while True:
      sets = self.sets_page(page_size=page_size, page_number=page_number, theme=theme, order_by=order_by, action=action, token=token, updated_since=updated_since)
      items.extend(sets)

      if len(sets) != page_size:
        break
      else:
        page_number += 1
        sleep(delay)

    return items

  def sets_page(self, page_size=250, page_number=1, theme=None, order_by=None, action=None, token='', updated_since=None):
    params = {'pageSize': page_size, 'pageNumber': page_number}

    if action:
      if action not in ['wanted', 'owned']:
        raise RuntimeError('ERROR: invalid action')

      if token is None:
        raise RuntimeError('ERROR: missing token')

      params.update({action: '1'})

    if theme:
      params.update({'theme': theme})

    if order_by:
      params.update({'orderBy': order_by})

    if updated_since:
      params.update({'updatedSince': updated_since})

    r = requests.get(
      self._base_url + '/getSets',
      params={
        'apiKey': self._api_key,
        'userHash': token,
        'params': json.dumps(self.sets_params(params))
      }
    )

    response = self.get_response(r)

    return response['sets']

  @staticmethod
  def sets_params(overrides):
    params = {
      'setID': '',
      'query': '',
      'theme': '',
      'subtheme': '',
      'setNumber': '',
      'year': '',
      'owned': '',
      'wanted': '',
      'updatedSince': '',
      'orderBy': 'Number',
      'pageSize': 250,
      'pageNumber': 1
    }
    params.update(overrides)
    return params

  @staticmethod
  def get_response(response):
    if response.status_code == 200 and response.json()['status'] == 'success':
      return response.json()
    else:
      raise RuntimeError(response.json()['message'])
