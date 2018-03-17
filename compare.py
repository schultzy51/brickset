#!/usr/bin/env python3

import argparse
import webbrowser

parser = argparse.ArgumentParser(description='Brickset Tooling', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('set_number', help='Set Number')

args = parser.parse_args()

urls = [
  'https://shop.lego.com/en-US/search/{}',
  'https://www.target.com/s?searchTerm=lego+{}',
  'https://www.walmart.com/search/?query=lego%20{}&cat_id=0',
  'https://www.toysrus.com/search?q=lego%20{}',
  'https://www.amazon.com/s/ref=nb_sb_noss?url=search-alias%3Daps&field-keywords=lego+{}',
  'https://www.ebay.com/sch/i.html?_from=R40&_nkw=lego+{}&_sacat=0&LH_BIN=1'
]

for url in urls:
  webbrowser.open_new_tab(url.format(args.set_number))
