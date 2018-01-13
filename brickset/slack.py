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

    if set['subtheme']:
      title += ' > {}'.format(set['subtheme'])

    title += ' > {}-{}'.format(set['number'], set['numberVariant'])

    if set['name']:
      title += ': {}'.format(set['name'])

    fields = []

    if set['year']:
      fields.append({
        "title": "Year",
        "value": set['year'],
        "short": True
      })

    if set['USRetailPrice']:
      fields.append({
        "title": "RRP",
        "value": set['USRetailPrice'],
        "short": True
      })

    if set['pieces']:
      fields.append({
        "title": "Pieces",
        "value": set['pieces'],
        "short": True
      })

    if False:
      fields.append({
        "title": "Last Updated",
        "value": '{}'.format(set['lastUpdated']),
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
        "image_url": set['imageURL'],
        "ts": set['lastUpdated'].timestamp()
      }
    ]

    self._client.chat.post_message(
      channel=self._channel,
      username=self._username,
      as_user=True,
      unfurl_links=False,
      attachments=attachments
    )
