#!/usr/bin/env python3

from brickset import read_jsonl
import os

if not os.path.exists('data'):
  raise RuntimeError('data directory missing!')

themes_file = os.path.join('data', 'themes.jsonl')
if not os.path.exists(themes_file):
  raise RuntimeError('themes.json missing!')

themes_directories = [name for name in os.listdir('data') if os.path.isdir(os.path.join('data', name))]

# TODO: check themes against directories
# TODO: check set count from themes.jsonl
# TODO: check subtheme count from themes.jsonl

for theme_directory in themes_directories:
  years_file = os.path.join('data', theme_directory, '{}_years.jsonl'.format(theme_directory))
  years = read_jsonl(years_file)

  years_set_count = 0
  for year in years:
    years_set_count += year['setCount']

  subthemes_file = os.path.join('data', theme_directory, '{}_subthemes.jsonl'.format(theme_directory))
  subthemes = read_jsonl(subthemes_file)

  subthemes_set_count = 0
  for subtheme in subthemes:
    subthemes_set_count += subtheme['setCount']

  sets_file = os.path.join('data', theme_directory, '{}_sets.jsonl'.format(theme_directory))
  sets = read_jsonl(sets_file)

  sets_set_count = len(sets)

  if years_set_count != sets_set_count:
    print("'{}' Year set count mismatch (expected={}, found={})".format(theme_directory, years_set_count, sets_set_count))

  if subthemes_set_count != sets_set_count:
    print("'{}' Subtheme set count mismatch (expected={}, found={})".format(theme_directory, subthemes_set_count, sets_set_count))

  # found_subtheme_count = len(subthemes) - 1  # subtract null subtheme
  # if found_subtheme_count != theme_subtheme_count:
  #   print("'{}' Subtheme count mismatch (expected={}, found={})".format(theme_name, theme_subtheme_count, found_subtheme_count))
  #   errors.extend({'theme': theme_name, 'type': 'subtheme count mismatch', 'expected': theme_subtheme_count, 'found': found_subtheme_count})
