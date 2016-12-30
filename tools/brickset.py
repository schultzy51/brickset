#!/usr/bin/env python3

import argparse
import simplejson as json
import zeep
from csv import DictWriter
from datetime import datetime
from io import StringIO
from time import sleep
from IPython import embed

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('-c', '--command', action='store', dest='command', help='Command to execute')
parser.add_argument('-a', '--api-key', action='store', dest='api_key', help='Developer api-key', required=True)
parser.add_argument('-u', '--username', action='store', dest='username', help='Username')
parser.add_argument('-p', '--password', action='store', dest='password', help='Password')
parser.add_argument('-m', '--minutes-ago', action='store', dest='minutes_ago', type=int, default=10080, help='Recent minutes ago')
parser.add_argument('-d', '--delay', action='store', dest='delay', type=int, default=2, help='Delay between api calls in seconds')
parser.add_argument('-t', '--theme', action='store', dest='theme', help='Theme')
parser.add_argument('-o', '--output', action='store', dest='output', default='jsonl', help='Output format')
parser.add_argument('-f', '--fields', dest='fields', action='store', default=[], nargs='+', help='Fields to output')

args = parser.parse_args()

print(args)

if args.output not in ['jsonl', 'csv']:
    raise ValueError('invalid output format')

client = zeep.Client('http://brickset.com/api/v2.asmx?WSDL')


def sets_params(overrides):
    params = {
        'apiKey': args.api_key,
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


def json_serial(obj):
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


objs = []

if args.command == 'recent':
    zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=args.api_key, minutesAgo=args.minutes_ago)
    objs = zeep.helpers.serialize_object(zeep_sets)

elif args.command == 'wanted':
    token = client.service.login(apiKey=args.api_key, username=args.username, password=args.password)
    zeep_sets = client.service.getSets(**sets_params({'userHash': token, 'wanted': 1}))
    objs = zeep.helpers.serialize_object(zeep_sets)

    # Custom sort
    objs.sort(key=lambda obj: obj['number'])
    objs.sort(key=lambda obj: obj['released'], reverse=True)
    objs.sort(key=lambda obj: (obj['USDateAddedToSAH'] is None, obj['USDateAddedToSAH']))

elif args.command == 'themes':
    zeep_themes = client.service.getThemes(apiKey=args.api_key)
    objs = zeep.helpers.serialize_object(zeep_themes)

elif args.command == 'subthemes':
    zeep_subthemes = client.service.getSubthemes(apiKey=args.api_key, theme=args.theme)
    objs = zeep.helpers.serialize_object(zeep_subthemes)

elif args.command == 'years':
    zeep_years = client.service.getYears(apiKey=args.api_key, theme=args.theme)
    objs = zeep.helpers.serialize_object(zeep_years)

elif args.command == 'sets':
    page_number = 1
    page_size = 50

    while True:
        params = sets_params({'theme': args.theme, 'pageSize': page_size, 'pageNumber': page_number})
        zeep_sets = client.service.getSets(**params)
        sets = zeep.helpers.serialize_object(zeep_sets)

        objs += sets

        if len(sets) != page_size:
            break
        else:
            page_number += 1
            sleep(args.delay)

else:
    print('Unknown Command')

if args.fields:
    for obj in objs:
        obj = OrderedDict((k, obj[k]) for k in args.fields if k in obj)

fp = StringIO()

if args.output == 'csv':
    # keys = ['setID', 'number', 'year', 'released', 'USDateAddedToSAH']
    # writer = DictWriter(fp, fieldnames=keys, extrasaction='ignore')
    keys = objs[0].keys()
    writer = DictWriter(fp, fieldnames=keys, extrasaction='ignore')
    writer.writeheader()
    for obj in objs:
        writer.writerow(obj)

elif args.output == 'jsonl':
    for obj in objs:
        fp.write(json.dumps(obj, default=json_serial) + '\n')

print(fp.getvalue())
