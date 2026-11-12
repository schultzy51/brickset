from datetime import datetime

from slacker import Slacker


class Slack:
  def __init__(self, api_key, channel, username):
    self._client = Slacker(api_key)
    self._channel = channel
    self._username = username

  def post_set(self, set):
    # TODO: build title (subtheme optional)
    # title = '{} > {} > {}-{}: {}'.format(set['theme'], set['subtheme'], set['number'], set['numberVariant'], set['name'])

    title = '{}'.format(set['theme'])

    if set.get('subtheme'):
      title += ' > {}'.format(set['subtheme'])

    title += ' > {}-{}'.format(set['number'], set['numberVariant'])

    if set.get('name'):
      title += ': {}'.format(set['name'])

    fields = []

    if set.get('year'):
      fields.append({
        "title": "Year",
        "value": set['year'],
        "short": True
      })

    retail_price = set.get('LEGOCom', {}).get('US', {}).get('retailPrice')
    if retail_price:
      fields.append({
        "title": "RRP",
        "value": retail_price,
        "short": True
      })

    if set.get('pieces'):
      fields.append({
        "title": "Pieces",
        "value": set['pieces'],
        "short": True
      })

    attachments = [
      {
        "fallback": title,
        # TODO: change color if wanted or owned
        "color": "#36a64f",
        "title": title,
        "title_link": set['bricksetURL'],
        "fields": fields,
        "image_url": set.get('image', {}).get('imageURL'),
      }
    ]

    if set.get('lastUpdated'):
      last_updated = datetime.fromisoformat(set['lastUpdated'].replace('Z', '+00:00'))
      attachments[0]['ts'] = last_updated.timestamp()

    self._client.chat.post_message(
      channel=self._channel,
      username=self._username,
      as_user=True,
      unfurl_links=False,
      attachments=attachments
    )
