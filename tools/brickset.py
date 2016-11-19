#!/usr/bin/python

import zeep
import argparse
from tabulate import tabulate

parser = argparse.ArgumentParser(description='Brickset Tooling')
parser.add_argument('command', help='Command to execute')
parser.add_argument('-a', '--api-key', action="store", dest="api_key", help='Developer api-key')
parser.add_argument('-u', '--username', action="store", dest="username", help='')
parser.add_argument('-p', '--password', action="store", dest="password", help='')
parser.add_argument('-m', '--minutes-ago', action="store", dest="minutes_ago", type=int, default=10080, help='')

args = parser.parse_args()
client = zeep.Client('http://brickset.com/api/v2.asmx?WSDL')

keys = (
    'number',
    'name',
    'year',
    'theme',
    'subtheme',
    'pieces',
    'released',
    'owned',
    'USRetailPrice',
    'USDateAddedToSAH',
    'USDateRemovedFromSAH',
    'lastUpdated'
)

if args.command == 'recent':
    zeep_sets = client.service.getRecentlyUpdatedSets(apiKey=args.api_key, minutesAgo=args.minutes_ago)
    sets = zeep.helpers.serialize_object(zeep_sets)
    sets = [dict((k, lego_set[k]) for k in keys) for lego_set in sets]
    print tabulate(sets, headers='keys')
elif args.command == 'wanted':
    token = client.service.login(apiKey=args.api_key, username=args.username, password=args.password)
    sets = client.service.getSets(
        apiKey=args.api_key,
        userHash=token,
        query='',
        theme='',
        subtheme='',
        setNumber='',
        year='',
        owned='',
        wanted=1,
        orderBy='',
        pageSize=100,
        pageNumber=1,
        userName=''
    )
    print sets
else:
    print 'Unknown Command'
