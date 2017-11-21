#!/usr/bin/env python3

from brickset import read_jsonl, parameterize
import os

if not os.path.exists('data'):
  raise RuntimeError('data directory missing!')

themes_file = os.path.join('data', 'themes.jsonl')
if not os.path.exists(themes_file):
  raise RuntimeError('themes.json missing!')

themes = read_jsonl(themes_file)

themes_directories = [name for name in os.listdir('data') if os.path.isdir(os.path.join('data', name))]
parameterized_theme_names = [parameterize(theme['theme'], sep='_') for theme in themes]

remote_missing_themes = list(set(themes_directories) - set(parameterized_theme_names))

if len(remote_missing_themes) > 0:
  print("Remove missing themes: {}".format(remote_missing_themes))

local_missing_themes = list(set(parameterized_theme_names) - set(themes_directories))

if len(local_missing_themes) > 0:
  print("Local missing themes: {}".format(local_missing_themes))

theme_dict = {}
for theme in themes:
  param_theme_name = parameterize(theme['theme'], sep='_')
  theme_dict[param_theme_name] = {'set_count': theme['setCount'], 'subtheme_count': theme['subthemeCount']}

# TODO: check set count from themes.jsonl

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

  found_subtheme_count = len(subthemes) - 1  # subtract null subtheme
  expect_subtheme_count = theme_dict[theme_directory]['subtheme_count']
  # some fuzzy math with subthemes
  if expect_subtheme_count - found_subtheme_count > 1 or found_subtheme_count - expect_subtheme_count > 0:
    print("'{}' Subtheme count mismatch (expected={}, found={})".format(theme_directory, expect_subtheme_count, found_subtheme_count))
