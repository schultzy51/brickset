#!/usr/bin/env python3

import argparse
import asyncio
import os
import re
import sys
import webbrowser
from dataclasses import asdict

import simplejson as json

from brickset import read_jsonl
from brickset.stores import SCRAPERS, check_prices

LIST_FILES = [os.path.join('lists', 'wanted.jsonl'), os.path.join('lists', 'owned.jsonl')]

parser = argparse.ArgumentParser(description='Find the best current price for a LEGO set across US stores', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('set_number', help="Set number, e.g. 43263 or 43263-1")
parser.add_argument('-s', '--stores', default=','.join(SCRAPERS), help='Comma-separated stores to check')
parser.add_argument('--show', action='store_true', help='Show the browser window (helps get past bot checks)')
parser.add_argument('-o', '--open', action='store_true', help='Open the best in-stock offer in your browser')
parser.add_argument('-j', '--json', action='store_true', help='Print JSON instead of a table')
parser.add_argument('-t', '--timeout', type=int, default=60, help='Seconds to allow each store')


def list_price_from_lists(number):
  for filename in LIST_FILES:
    if not os.path.isfile(filename):
      continue
    for s in read_jsonl(filename):
      if str(s.get('number')) == number:
        price = s.get('retailPrice') or (((s.get('LEGOCom') or {}).get('US') or {}).get('retailPrice'))
        if price:
          return float(price), s.get('name')
  return None, None


def money(value):
  return '' if value is None else '${:,.2f}'.format(value)


def vs_list(total, list_price):
  if total is None or not list_price:
    return ''
  pct = (total - list_price) / list_price * 100
  return 'list' if abs(pct) < 0.5 else '{:+.0f}%'.format(pct)


def stock(offer):
  return {True: 'in stock', False: 'OUT', None: '?'}[offer.in_stock]


def print_report(number, name, list_price, results):
  print('{}{}  ·  list price {}'.format(number, ' ' + name if name else '', money(list_price) or 'unknown'))
  print()

  offers = [o for r in results for o in r.offers if o.price is not None]
  offers.sort(key=lambda o: (o.in_stock is False, o.total))

  if offers:
    print('{:<24} {:>10} {:>9} {:>10} {:>7}  {:<9} {}'.format('store', 'price', 'shipping', 'total', 'vs list', 'stock', 'seller'))
    for o in offers:
      shipping = 'free' if o.shipping == 0 else (money(o.shipping) if o.shipping is not None else '?')
      print('{:<24} {:>10} {:>9} {:>10} {:>7}  {:<9} {}'.format(
        o.store[:24], money(o.price), shipping, money(o.total), vs_list(o.total, list_price), stock(o), (o.seller or '')[:24]))

    best = next((o for o in offers if o.in_stock is not False), None)
    print()
    if best:
      print('Best: {} {} ({}){}'.format(best.store, money(best.total), vs_list(best.total, list_price) or 'no list price',
                                         '' if best.shipping is not None else ' + shipping'))
      print('      {}'.format(best.url))
    else:
      print('No in-stock offers found.')
  else:
    print('No offers found.')

  notes = [r for r in results if r.status != 'ok']
  if notes:
    print()
    for r in notes:
      label = {'not_found': 'not listed', 'blocked': 'blocked by bot check (try --show)',
               'error': 'failed', 'link_only': 'not checked'}.get(r.status, r.status)
      print('{:<24} {}{}{}'.format(r.store, label, ': ' + r.message if r.message else '', '  ' + r.url if r.url else ''))

  return offers


args = parser.parse_args()

number = re.sub(r'-\d+$', '', args.set_number.strip())
if not re.fullmatch(r'[0-9A-Za-z]+', number):
  sys.exit('Not a set number: {}'.format(args.set_number))

stores = [s.strip().lower() for s in args.stores.split(',') if s.strip()]
unknown = [s for s in stores if s not in SCRAPERS]
if unknown:
  sys.exit('Unknown store(s): {} (choose from {})'.format(', '.join(unknown), ', '.join(SCRAPERS)))

try:
  list_price, name = list_price_from_lists(number)
  results, list_price = asyncio.run(check_prices(number, stores, list_price=list_price, headless=not args.show, timeout=args.timeout))
  name = name or next((o.title for r in results if r.store == 'LEGO.com' for o in r.offers), None)

  if args.json:
    print(json.dumps({'number': number, 'name': name, 'list_price': list_price,
                      'results': [asdict(r) for r in results]}, ignore_nan=True))
    offers = [o for r in results for o in r.offers if o.price is not None]
  else:
    offers = print_report(number, name, list_price, results)

  if args.open:
    best = next((o for o in sorted(offers, key=lambda o: o.total) if o.in_stock is not False), None)
    if best and best.url:
      webbrowser.open_new_tab(best.url)

except Exception as e:
  sys.exit(e)
