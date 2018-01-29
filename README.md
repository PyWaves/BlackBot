# BlackBot

BlackBot is a Python bot implementing a grid trading strategy. It can work with any assets pair on the Waves DEX.

Grid trading doesn’t care about which way the market’s going — in fact, as a profitable strategy it works best in ranging markets. The strategy places a ladder of sells at regular intervals above market price, and another ladder of buys beneath it. If a sell is filled, those funds are used to place a buy just beneath that sell. Thus you can think of the grid as a series of pairs of buys/sells stretching up and down the price chart, with either the buy or sell in each pair always active.

For example, let’s say the last price is 2000 satoshis you’ve got sells laddered up at 2100, 2200, 2300… If the price hits 2100, you immediately use those funds to place a new buy at 2000. If it drops to 2000 again, you buy back the Incent you sold at 2100. If it rises further, you sell at 2200 and open a buy at 2100. Whichever way the price moves, you’re providing depth — buffering the market and smoothing out any peaks and troughs. Additionally, if you open and then close a trade within a tranche (e.g. you sell at 2200, then buy back at 2100) then you make a small profit.

## Getting Started

You can start BlackBot with this command:

```
python BlackBot.py sample-bot.cfg
```

below you can find a sample configuration file:
```
[main]
node = http://nodes.wavesnodes.com
matcher = http://nodes.wavesnodes.com
order_fee = 300000
order_lifetime = 86400

[account]
private_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

[market]
amount_asset = WAVES
price_asset = 8LQW8f7P5d5PZM7GtZEBgaqRPGSzS3DfPuiXrURJ4AJS

[grid]
interval = 0.005
tranche_size = 200000000
grid_levels = 20
base = last
type = symmetric
 
[logging]
logfile = bot.log
```

#### main section
```node``` is the address of the fullnode

```matcher``` is the matcher address

```order_fee``` is the fee to place buy and sell orders

```order_lifetime``` is the maximum life time (in seconds) for an open order

#### account section
```private_key``` is the private key of the trading account

#### market section
```amount_asset``` and ```price_asset``` are the IDs of the traded assets pair

#### grid section
```interval``` is the % interval between grid levels

```tranche_size``` is the size amount of each buy and sell order

```grid_levels``` is the number of grid levels

```base``` is the price level around which the grid is setup; it can be LAST, for the last traded price, BID for the current bid price, ASK for the current ask price or a fixed constant price can be specified

```type``` the initial grid can be SYMMETRIC, if there are both buy and sell orders; BIDS if the are only buy orders; ASKS if there are only sell orders

#### logging section
```logfile``` is the file where the log will be written
