from slackbot.bot import respond_to
from brickset import filter_keys
from brickset.service import Brickset
from brickset.config import get_config
import re

config = get_config(section='wanted')

@respond_to('recent', re.IGNORECASE)
def recent(message):
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  sets = brickset.recent(1440)
  sets.reverse()
  sets = filter_keys(sets, config['output']['recent'])

  for set in sets:
    print(set)
    message.reply(set['name'])

