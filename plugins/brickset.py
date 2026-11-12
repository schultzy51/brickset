from slackbot.bot import respond_to
from brickset import filter_keys
from brickset.service_v2 import Brickset
from brickset.config import get_config
from datetime import datetime, timedelta, timezone
import re

config = get_config(section='wanted')

@respond_to('recent', re.IGNORECASE)
def recent(message):
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
  sets = brickset.recent(yesterday)
  sets.reverse()
  sets = filter_keys(sets, config['output']['recent'])

  for set in sets:
    print(set)
    message.reply(set['name'])

