# brickset

```
pip3 install -r requirements.txt
```

A script to assist with determining the optimal order

```
./brickset.py themes | jq -c '.[]'
./brickset.py -m 10080 -o recent | jq -c '.[]'
./brickset.py -s wanted set_order | jq -c '.[]'
```
