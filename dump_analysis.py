#!/usr/bin/env python3

from brickset import read_jsonl, parameterize
import os

# check for data directory
if not os.path.exists('data'):
  raise RuntimeError('data directory missing!')

# check for data/themes.jsonl
themes_file = os.path.join('data', 'themes.jsonl')
if not os.path.exists(themes_file):
  raise RuntimeError('themes.json missing!')

themes = read_jsonl(themes_file)

# compare theme directories against themes.jsonl
themes_directories = [name for name in os.listdir('data') if os.path.isdir(os.path.join('data', name))]
parameterized_theme_names = [parameterize(theme['theme'], sep='_') for theme in themes]

remote_missing_themes = list(set(themes_directories) - set(parameterized_theme_names))

if len(remote_missing_themes) > 0:
  print("Remove missing themes: {}".format(remote_missing_themes))

local_missing_themes = list(set(parameterized_theme_names) - set(themes_directories))

if len(local_missing_themes) > 0:
  print("Local missing themes: {}".format(local_missing_themes))

# create dict of theme set and subtheme counts
theme_dict = {}
for theme in themes:
  param_theme_name = parameterize(theme['theme'], sep='_')
  theme_dict[param_theme_name] = {'set_count': theme['setCount'], 'subtheme_count': theme['subthemeCount']}

# check each theme
for theme_directory in themes_directories:
  # load years
  years_file = os.path.join('data', theme_directory, '{}_years.jsonl'.format(theme_directory))
  years = read_jsonl(years_file)

  # load subthemes
  subthemes_file = os.path.join('data', theme_directory, '{}_subthemes.jsonl'.format(theme_directory))
  subthemes = read_jsonl(subthemes_file)

  # load sets
  sets_file = os.path.join('data', theme_directory, '{}_sets.jsonl'.format(theme_directory))
  sets = read_jsonl(sets_file)

  # sum set counts from years
  years_set_count = 0
  for year in years:
    years_set_count += year['setCount']

  # sum set counts from subthemes
  subthemes_set_count = 0
  for subtheme in subthemes:
    subthemes_set_count += subtheme['setCount']

  sets_set_count = len(sets)

  # check set counts
  if years_set_count != sets_set_count:
    print("'{}' Year set count mismatch (expected={}, found={})".format(theme_directory, years_set_count, sets_set_count))

  found_set_count = len(sets)
  expected_set_count = theme_dict[theme_directory]['set_count']
  if expected_set_count != found_set_count:
    print("'{}' Set count mismatch (expected={}, found={})".format(theme_directory, expected_set_count, found_set_count))

  # check subtheme counts
  if subthemes_set_count != sets_set_count:
    print("'{}' Subtheme set count mismatch (expected={}, found={})".format(theme_directory, subthemes_set_count, sets_set_count))

  found_subtheme_count = len(subthemes) - 1  # subtract null subtheme
  expected_subtheme_count = theme_dict[theme_directory]['subtheme_count']
  # some fuzzy math with subthemes
  if expected_subtheme_count - found_subtheme_count > 1 or found_subtheme_count - expected_subtheme_count > 0:
    print("'{}' Subtheme count mismatch (expected={}, found={})".format(theme_directory, expected_subtheme_count, found_subtheme_count))
