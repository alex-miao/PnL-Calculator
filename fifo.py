import argparse
import csv
import time

parser = argparse.ArgumentParser(description="Process input CSV file")
parser.add_argument("file", help="CSV file to process")
args = parser.parse_args()

with open(args.file, 'r') as f:
    reader = csv.reader(f)
    tx_list = list(reader)

#dictionary that maps asset names to dictionary with amount owned, latest price, and P&L
assets = {}

error = 0 #different error codes for different errors
error_var = 0 #variable to pass to error message
i = 1

#iterate down list of transactions until we reach end of list or encounter an error
while i < len(tx_list) and error == 0:
    entry = tx_list[i]
    date = time.strptime(entry[0].strip(), "%m/%d/%Y")
    asset = entry[1].strip().upper()
    price = float(entry[2].strip())
    amount = float(entry[3].strip())

    #Check if ticker name is legal
    if (not asset.isalpha()) or len(asset) < 3 or len(asset) > 6:
        error = 1
        error_var = asset

    #make sure no USD transactions
    if asset == "USD":
        error = 2

    #do not allow negative prices
    if price < 0:
        error = 3

    if asset in assets:
        if assets[asset]['amount'] + amount < 0: #prevents selling more shares than you own
            error = 4
        elif assets[asset]['last_date'] > date: #makes sure dates are in order (at least for each asset)
            error = 5
        else:
            if amount >= 0:
                assets[asset]['avg_open_price'] = (assets[asset]['avg_open_price'] * assets[asset]['amount'] + price * amount) / (assets[asset]['amount'] + amount)
                assets[asset]['amount'] += amount
                assets[asset]['last_price'] = price
                assets[asset]['last_date'] = date
            else:
                assets[asset]['pnl_realized'] -= (price - assets[asset]['avg_open_price']) * amount
                assets[asset]['amount'] += amount
                assets[asset]['pnl_unrealized'] = (price - assets[asset]['avg_open_price']) * assets[asset]['amount']
                assets[asset]['last_price'] = price
                assets[asset]['last_date'] = date
    else:
        if amount < 0: #prevents selling more shares than you own
            error = 4
        else:
            assets[asset] = {}
            assets[asset]['avg_open_price'] = price
            assets[asset]['pnl_realized'] = 0
            assets[asset]['pnl_unrealized'] = 0
            assets[asset]['amount'] = amount
            assets[asset]['last_price'] = price
            assets[asset]['last_date'] = date
    i += 1

outputFile = args.file.split(".")[0] + '.out'
f = open(outputFile, "w+")
if error == 0:
    numAssets = len(assets)

    if numAssets == 1:
        f.write("Portfolio " + "(" + str(numAssets) + " asset) \n")
    else:
        f.write("Portfolio " + "(" + str(numAssets) + " assets) \n")

    total_value = 0
    for asset in assets:
        total_value += assets[asset]['amount'] * assets[asset]['last_price']
        f.write(asset + ": " + str(assets[asset]['amount']) + " $" + '%.2f' % (assets[asset]['amount'] * assets[asset]['last_price']) + "\n")

    f.write("Total portfolio value: $" + '%.2f' % total_value + "\n")

    if numAssets == 1:
        f.write("Portfolio P&L " + "(" + str(numAssets) + " asset): \n")
    else:
        f.write("Portfolio P&L " + "(" + str(numAssets) + " assets): \n")

    total_pnl = 0
    for asset in assets:
        total_pnl += assets[asset]['pnl_realized']
        f.write(asset + ": $" + '%.2f' % assets[asset]['pnl_realized'] + "\n")

    f.write("Total P&L: " + "$" + '%.2f' % total_pnl + "\n")
elif error == 1:
    f.write("Error: illegal ticker name - " + error_var +  " (names must be 3-6 letters)")
elif error == 2:
    f.write("Error: cannot make USD transaction")
elif error == 3:
    f.write("Error: can't have negative price")
elif error == 4:
    f.write("Error: detected sale before purchase (short selling is not supported)")
elif error == 5:
    f.write("Error: out of order dates for transactions")

f.close()
