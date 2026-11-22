#!/usr/bin/env python3

import argparse
import os
import simplejson as json
import sys
import webbrowser
from datetime import datetime, timedelta, timezone
from time import sleep

from brickset import filter_keys, json_serial, read_jsonl
from brickset.service_v2 import Brickset
from brickset.config import get_config
from brickset.slack import Slack

LAST_CHECK_FILE = 'last_recent_check.txt'
SEEN_FILE = 'recent_seen.txt'
WANTED_FILE = os.path.join('lists', 'wanted.jsonl')

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-us', '--updated-since', action='store', dest='updated_since', help="Updated Since 'yyyy-mm-dd' (default: {}, else 7 days ago)".format(LAST_CHECK_FILE))
parser.add_argument('-s', '--section', action='store', dest='section', default='default', help='Section')
parser.add_argument('-o', '--open-web', action='store_true', dest='open_web', help='Open a web tab for each set found')
parser.add_argument('-c', '--slack', action='store_true', dest='slack', help='Slack')
parser.add_argument('-e', '--epoch', action='store', dest='epoch', type=int, help='Last checked epoch')
parser.add_argument('-i', '--image-only', action='store_true', dest='image', help='Only sets with an image')
parser.add_argument('-a', '--all', action='store_true', dest='show_all', help='Include sets already shown in a previous run ({})'.format(SEEN_FILE))
parser.add_argument('-n', '--no-save', action='store_true', dest='no_save', help='Do not update {} or {}'.format(LAST_CHECK_FILE, SEEN_FILE))


def read_last_check():
  if os.path.isfile(LAST_CHECK_FILE):
    with open(LAST_CHECK_FILE) as f:
      value = f.read().strip()
    if value:
      datetime.strptime(value, '%Y-%m-%d')  # fail loudly on a malformed file
      return value

  return None


def read_seen():
  if not os.path.isfile(SEEN_FILE):
    return set()

  with open(SEEN_FILE) as f:
    return {int(line) for line in f if line.strip()}


def save_state(seen, shown_sets):
  seen = seen | {s['setID'] for s in shown_sets}
  with open(SEEN_FILE, 'w') as f:
    f.writelines('{}\n'.format(set_id) for set_id in sorted(seen))

  # keep a day of overlap; the seen list filters out the repeats
  since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
  with open(LAST_CHECK_FILE, 'w') as f:
    f.write('{}\n'.format(since))

  return since


def highlight_keys(config):
  # (theme, subtheme) pairs from the wanted list, plus whole themes from config
  pairs = set()
  if os.path.isfile(WANTED_FILE):
    pairs = {(s.get('theme'), s.get('subtheme')) for s in read_jsonl(WANTED_FILE)}

  themes = set(config.get('highlight_themes') or [])

  return pairs, themes


def is_highlight(rset, pairs, themes):
  return rset.get('theme') in themes or (rset.get('theme'), rset.get('subtheme')) in pairs


args = parser.parse_args()

items = []

try:
  config = get_config(section=args.section)
  brickset = Brickset(config['api_key'], config['username'], config['password'])

  if args.epoch:
    args.updated_since = datetime.fromtimestamp(args.epoch, timezone.utc).strftime('%Y-%m-%d')

  if not args.updated_since:
    args.updated_since = read_last_check() or (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')

  if not brickset.check_key():
    sys.exit('Invalid Key')

  sets = brickset.recent(args.updated_since) or []
  fetched = len(sets)

  unwanted_themes = config.get('unwanted_themes') or []

  if args.image:
    sets = list(filter(lambda d: d['image'], sets))

  sets = list(filter(lambda d: d['theme'] not in unwanted_themes, sets))
  sets = list(filter(lambda d: d['year'] > (datetime.now(timezone.utc).year - 1), sets))

  seen = read_seen()
  if not args.show_all:
    sets = [s for s in sets if s['setID'] not in seen]

  sets.reverse()

  pairs, themes = highlight_keys(config)
  highlighted = {s['setID'] for s in sets if is_highlight(s, pairs, themes)}
  sets.sort(key=lambda s: s['setID'] not in highlighted)  # stable: highlighted first

  print('Updated since {}: {} fetched, {} new, {} in themes you want'.format(
    args.updated_since, fetched, len(sets), len(highlighted)), file=sys.stderr)

  if args.open_web:
    total_sets = len(sets)
    for i, rset in enumerate(sets):
      webbrowser.open(rset['bricksetURL'], new=0, autoraise=False)
      if (i + 1) % 10 == 0 and i + 1 < total_sets:
        input("Press Enter to continue...({}/{})".format(i + 1, total_sets))
      else:
        sleep(5)

  if args.slack:
    slack = Slack(config['slack_api_token'], config['slack_channel'], config.get('slack_username'))
    for rset in sets:
      slack.post_set(rset, highlight=rset['setID'] in highlighted)

  if not args.no_save:
    since = save_state(seen, sets)
    print('Next run starts from {}'.format(since), file=sys.stderr)

  sets = filter_keys(sets, config['output']['recent'])
  items.extend(sets)

except Exception as e:
  sys.exit(e)
else:
  if not args.open_web:
    print(json.dumps(items, default=json_serial))
