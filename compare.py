#!/usr/bin/env python3

import argparse
import webbrowser

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('set_number', help='Set Number')

args = parser.parse_args()

urls = [
  'https://www.iwantoneofthose.com/elysium.search?search=lego+{}',
  'https://www.target.com/s?searchTerm=lego+{}',
  'https://www.walmart.com/search/?cat_id=0&query=lego+{}',
  'https://www.barnesandnoble.com/s/lego+{}',
  'https://www.amazon.com/s?k=lego+{}',
  'https://www.ebay.com/sch/i.html?_nkw=lego+{}',
  'https://www.lego.com/en-US/search?q={}'
]

for url in urls:
  webbrowser.open_new_tab(url.format(args.set_number))
