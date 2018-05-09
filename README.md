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
```
./recent.py -m 10000 -ms 0 -o'
./recent.py -e `cat last_recent_check.txt` -o'
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
