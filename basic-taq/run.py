#!/usr/bin/env python3

import raw_taq
import pandas as pd
import numpy as np
from statistics import mode, StatisticsError

def print_stats(chunk):
    #find the max bid price
    max_price = max(chunk['Bid_Price'])

    #find the min bid price
    min_price = min(chunk['Bid_Price'])

    #find the mean of bid price
    avg_price = np.mean(chunk['Bid_Price'])

    #find the mod of bid price
    try:
        mod_price = mode(chunk['Bid_Price'])
    except StatisticsError:
        mod_price = np.nan

    #find the sd of bid price
    sd_price = np.std(chunk['Bid_Price'])

    print("Max bid price: ", max_price, "\n", "Min bid price: ", min_price, "\n",
          "Mean bid price: ", avg_price, "\n", "Mod bid price: ", mod_price, "\n",
          "Standard deviation bid price: ", sd_price)

def process_chunks(taq):
    chunk_gen = taq.convert_taq(20)
    first_chunk = next(chunk_gen)
    curr_symbol = first_chunk['Symbol_root'][0]

    accum = pd.DataFrame(first_chunk)

    processed_symbols = 0
    for chunk in chunk_gen:
        where_symbol = curr_symbol == chunk['Symbol_root']
        if where_symbol.all():
            accum.append(pd.DataFrame(chunk))
        else:
            same = chunk[where_symbol]
            accum.append(pd.DataFrame(same))

            # Compute the stats
            print('Current symbol:', curr_symbol, len(curr_symbol), 'records')
            print_stats(accum)
            processed_symbols += 1
            if processed_symbols > 3:
                break

            diff = chunk[~where_symbol]
            accum = pd.DataFrame(diff)
            curr_symbol = accum.Symbol_root[0]

if __name__ == '__main__':
    # I grab the [0]'th fname in the glob
    # fname = '../local_data/EQY_US_ALL_BBO_20150102.zip'
    # fname = '../local_data/EQY_US_ALL_BBO_20140206.zip'
    from sys import argv
    fname = '../local_data/EQY_US_ALL_BBO_201501' + argv[1] + '.zip'
    print("processing", fname)
    local_taq = raw_taq.TAQ2Chunks(fname)

    process_chunks(local_taq)
