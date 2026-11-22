# brickset

## Setup

```
pip3 install -r requirements.txt
```

## Scripts

Update the optimal purchase order for wanted sets and owned sets

```
./update.py
```

For simple bricket api calls

```
./command.py themes | jq -c '.[]'
```

View recently updated sets

By default this picks up where the last run left off (`last_recent_check.txt`), skips sets
already shown in an earlier run (`recent_seen.txt`), and lists sets whose theme/subtheme
matches your wanted list first. Add `highlight_themes: [...]` to `.config.yml` to always
flag whole themes.
```
./recent.py -o          # open new sets in the browser, then save state
./recent.py -c -i       # post new sets with images to Slack
./recent.py -us 2026-01-01 -a -n   # ad hoc: everything since a date, don't touch state
```

Dump the sets for statistical analysis
```
./dump.py
./dump_analysis.py
./dump_convert.py
```

Slackbot for recent sets

```
SLACKBOT_API_TOKEN=#### ./slackbot_run.py
```

Back up instruction manuals for owned sets
```
./get_instructions.py
```

## Ideas
