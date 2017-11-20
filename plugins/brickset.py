from slackbot.bot import respond_to
from brickset.service import Brickset
from brickset.config import get_config
from datetime import datetime
import re

config = get_config(section='wanted')

def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


def filter_keys(items, wanted_keys):
  return [{k: v for (k, v) in item.items() if k in wanted_keys} for item in items]

@respond_to('recent', re.IGNORECASE)
def recent(message):
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  sets = brickset.recent(1440)
  sets.reverse()
  sets = filter_keys(sets, config['output']['recent'])

  for set in sets:
    print(set)
    message.reply(set['name'])

