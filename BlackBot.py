import pywaves as pw
import datetime
import time
import os
import sys
import random
try:
	import configparser
except ImportError:
	import ConfigParser as configparser


COLOR_RESET = "\033[0;0m"
COLOR_GREEN = "\033[0;32m"
COLOR_RED = "\033[1;31m"
COLOR_BLUE = "\033[1;34m"
COLOR_WHITE = "\033[1;37m"


def log(msg):
    timestamp = datetime.datetime.utcnow().strftime("%b %d %Y %H:%M:%S UTC")
    s = "[%s] %s:%s %s" % (timestamp, COLOR_WHITE, COLOR_RESET, msg)
    print(s)
    try:
        f = open(LOGFILE, "a")
        f.write(s + "\n")
        f.close()
    except:
        pass


def grid_price(level):
    return int(basePrice * (1 + INTERVAL) ** (level - GRID_LEVELS / 2))


def place_order(order_type, level):
    if 0 <= level < GRID_LEVELS and (grid[level] == "" or grid[level] == "-"):
        price = grid_price(level)
        price = int(price / 100) * 100
        price = round(price / 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals)), 8)
        price = float(str(price))
        try:
            balance_amount, balance_price = BLACKBOT.tradableBalance(PAIR)
            tranche_size = int(TRANCHE_SIZE * (1 - (FLEXIBILITY / float(200)) + (random.random() * FLEXIBILITY / float(100))))
            if order_type == "buy" and balance_price >= (tranche_size * price / 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals))):
                o = BLACKBOT.buy(PAIR, tranche_size, price, maxLifetime=ORDER_LIFETIME, matcherFee=ORDER_FEE)
            elif order_type == "sell":# and balance_amount >= (tranche_size * price / 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals))):
                #price -= 1
                o = BLACKBOT.sell(PAIR, tranche_size, price, maxLifetime=ORDER_LIFETIME, matcherFee=ORDER_FEE)
            id = o.orderId
            log(">> [%03d] %s%-4s order  %18.*f%s" % (level, COLOR_GREEN if order_type == "buy" else COLOR_RED, order_type.upper(), PAIR.asset2.decimals, price, COLOR_RESET))
        except:
            id = ""
        grid[level] = id


def get_last_price():
    try:
        last_trade_price = int(float(PAIR.trades(1)[0]['price']) * 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals)))
    except:
        last_trade_price = 0
    return last_trade_price


CMD = ""
CFG_FILE = ""

if len(sys.argv) >= 2:
    CFG_FILE = sys.argv[1]

if len(sys.argv) == 3:
    CMD = sys.argv[2].upper()

if not os.path.isfile(CFG_FILE):
    log("Missing config file")
    log("Exiting.")
    exit(1)

# parse config file
try:
    log("%sReading config file '%s'" % (COLOR_RESET, CFG_FILE))
    config = configparser.RawConfigParser()
    config.read(CFG_FILE)

    NODE = config.get('main', 'node')
    MATCHER = config.get('main', 'matcher')
    ORDER_FEE = config.getint('main', 'order_fee')
    ORDER_LIFETIME = config.getint('main', 'order_lifetime')

    PRIVATE_KEY = config.get('account', 'private_key')
    amountAssetID = config.get('market', 'amount_asset')
    priceAssetID = config.get('market', 'price_asset')

    INTERVAL = config.getfloat('grid', 'interval')
    TRANCHE_SIZE = config.getint('grid', 'tranche_size')
    FLEXIBILITY = config.getint('grid', 'flexibility')
    GRID_LEVELS = config.getint('grid', 'grid_levels')
    GRID_BASE = config.get('grid', 'base').upper()
    GRID_TYPE = config.get('grid', 'type').upper()

    LOGFILE = config.get('logging', 'logfile')

    BLACKBOT = pw.Address(privateKey=PRIVATE_KEY)

    log("-" * 80)
    log("          Address : %s" % BLACKBOT.address)
    log("  Amount Asset ID : %s" % amountAssetID)
    log("   Price Asset ID : %s" % priceAssetID)
    log("-" * 80)
    log("")
except:
    log("Error reading config file")
    log("Exiting.")
    exit(1)

pw.setNode(NODE, "mainnet")
pw.setMatcher(MATCHER)
PAIR = pw.AssetPair(pw.Asset(amountAssetID), pw.Asset(priceAssetID))

# grid list with GRID_LEVELS items. item n is the ID of the order placed at the price calculated with this formula
# price = int(basePrice * (1 + INTERVAL) ** (n - GRID_LEVELS / 2))

grid = ["-"] * GRID_LEVELS

log("Cancelling open orders...")

# cancel all open orders on the specified pair
BLACKBOT.cancelOpenOrders(PAIR)
log("Deleting order history...")

# delete order history on the specified pair
BLACKBOT.deleteOrderHistory(PAIR)
log("")

# terminate if RESET argument is given on the command line
if CMD == "RESET":
    log("Exiting.")
    exit(1)

# initialize grid
try:
    if GRID_BASE.isdigit():
        basePrice = int(GRID_BASE)
    elif GRID_BASE == "LAST":
        basePrice = get_last_price()
    elif GRID_BASE == "BID":
        basePrice = PAIR.orderbook()['bids'][0]['price']
    elif GRID_BASE == "ASK":
        basePrice = PAIR.orderbook()['asks'][0]['price']
except:
    basePrice = 0
if basePrice == 0:
    log("Invalid BASE price")
    log("Exiting.")
    exit(1)

#log("Grid initialisation [base price : %.*f]" % (PAIR.asset2.decimals, float(basePrice) / 10 ** PAIR.asset2.decimals))
log("Grid initialisation [base price : %.*f]" % (PAIR.asset2.decimals, float(basePrice) / 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals))))

last_level = int(GRID_LEVELS / 2)

if GRID_TYPE == "SYMMETRIC" or GRID_TYPE == "BIDS":
    for n in range(last_level - 1, -1, -1):
        place_order("buy", n)
if GRID_TYPE == "SYMMETRIC" or GRID_TYPE == "ASKS":
    for n in range(last_level + 1, GRID_LEVELS):
        place_order("sell", n)

# loop forever
while True:
    # attempt to retrieve order history from matcher
    try:
        history = BLACKBOT.getOrderHistory(PAIR)
    except:
        history = []

    if history:
        # loop through all grid levels
        # first all ask levels from the lowest ask to the highest -> range(grid.index("") + 1, len(grid))
        # then all bid levels from the highest to the lowest -> range(grid.index("") - 1, -1, -1)
        for n in list(range(last_level + 1, len(grid))) + list(range(last_level - 1, -1, -1)):

            # find the order with id == grid[n] in the history list

            order = [item for item in history if item['id'] == grid[n]]
            status = order[0].get("status") if order else ""
            if status == "Filled":
                BLACKBOT.deleteOrderHistory(PAIR)
                last_price = get_last_price()
                grid[n] = ""
                last_level = n
                filled_price = order[0].get("price")
                filled_type = order[0].get("type")
                log("## [%03d] %s%-4s Filled %18.*f%s" % (n, COLOR_BLUE, filled_type.upper(), PAIR.asset2.decimals, float(filled_price) / 10 ** (PAIR.asset2.decimals + (PAIR.asset2.decimals - PAIR.asset1.decimals)), COLOR_RESET))

                if filled_type == "buy":
                    if filled_price >= last_price:
                        place_order("sell", n + 1)
                    else:
                        place_order("buy", n)
                elif filled_type == "sell":
                    if filled_price <= last_price:
                        place_order("buy", n - 1)
                    else:
                        place_order("sell", n)
            # attempt to place again orders for empty grid levels or cancelled orders
            elif (status == "" or status == "Cancelled") and grid[n] != "-":
                grid[n] = ""
                if n > last_level:
                    place_order("sell", n)
                elif n < last_level:
                    place_order("buy", n)
    time.sleep(5)
