from datetime import datetime
import jsonlines
import simplejson as json


def json_serial(obj):
  if isinstance(obj, datetime):
    serial = obj.isoformat()
    return serial
  raise TypeError("Type not serializable")


def filter_keys(items, wanted_keys):
  return [{k: v for (k, v) in item.items() if k in wanted_keys} for item in items]


def write_jsonl(filename, items):
  with jsonlines.open(filename, mode='w', dumps=json.JSONEncoder(default=json_serial).encode) as writer:
    writer.write_all(items)


def read_jsonl(filename):
  items = []
  with jsonlines.open(filename) as reader:
    for item in reader:
      items.append(item)

  return items
