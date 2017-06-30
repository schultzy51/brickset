# brickset

A script to assist with determining the optimal order

```
./tools/brickset.py themes | jq '.[]'
./tools/brickset.py -m 10080 -o recent | jq -c '.[]'
./tools/brickset.py -s wanted set_order | jq -c '.[]'
```