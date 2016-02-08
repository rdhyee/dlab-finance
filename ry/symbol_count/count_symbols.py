#!/global/home/users/ryee/miniconda/envs/myenv3/bin/python

from glob import glob
import os
from itertools import (islice, zip_longest)
from collections import Counter
from sys import argv
import time, datetime
import argparse
import re

import pytz, arrow

import numpy as np
import tables as tb


import raw_taq



def count_chunk_elements1(fname, chunksize=1000000, max_chunk=None, process_chunk=False):

    symbol_roots = Counter()

    for (i,chunk) in enumerate(islice(raw_taq.TAQ2Chunks(fname, 
                                                         chunksize=chunksize, 
                                                         process_chunk=process_chunk), max_chunk)):

        counts = np.unique(chunk[:]['Symbol_root'], return_counts=True)
        symbol_roots.update(dict(zip_longest(counts[0], counts[1])))

        #print("\r {0}".format(i),end="")

    return symbol_roots



def timestamp_for_trading_date(year,month,day):
    
    eastern = pytz.timezone('US/Eastern')
    return arrow.get(eastern.localize(datetime.datetime(year,month,day))).timestamp


def bbo_path_to_datetime(path):
    """
    takes a path to a file and returns the datetime.datetime for midnight of the date
    
    assumption that filename has form {label_date.zip}
    """

    g = re.search(r'(\d{4})(\d{2})(\d{2}).zip', path)
    if g:
        eastern = pytz.timezone('US/Eastern')
        return eastern.localize(datetime.datetime(*map(int,g.groups())))
    else:
        return None
    

def datetime_to_bbo_path(d):
    """
    takes input d (datetime.date) and returns a string with the full path to the corresponding BBO file
    """
    return "{base_dir}/{label}_{year:04d}/{label}_{year:04d}{month:02d}/{label}_{year:04d}{month:02d}{day:02d}.zip".format(
              base_dir=BBO_BASE_DIR,
              label=BBO_LABEL,
              year=d.year, month=d.month, day=d.day)


class SymbolCount(tb.IsDescription):
    symbol_root  = tb.StringCol(6, pos=1)
    count = tb.Int32Col(pos=2)   # short integer
    date = tb.Int32Col(pos=3)

def write_h5_for_counter(ct, timestamp, h5_path):
    with tb.open_file(h5_path, mode="w") as countfile:
        root = countfile.root
        c_table = countfile.createTable(root, "count_table", SymbolCount )
        
        # convert ct to rows
        # fill in timestamp for all the rows
        rows = [(symbol, count, timestamp) for (symbol, count) in ct.items()]
        
        c_table.append(rows)
        c_table.flush()
    


if __name__ == '__main__':


    # read in the file name
    parser = argparse.ArgumentParser()

    parser.add_argument("fname", help="TAQ BBO zip file to process")
    parser.add_argument('-max_chunk', dest='max_chunk', action='store', help='max chunk to process', default=None)
    
    args = parser.parse_args()
  
    
    if args.max_chunk is not None:
        max_chunk = int(args.max_chunk)
    else:
        max_chunk = None


    t0 = time.time()

    # do the calculation only lif h5_path doesn't exist

    file_dt = bbo_path_to_datetime(args.fname)
    (year, month, day) = arrow.get(file_dt).timetuple()[0:3]
    ts = timestamp_for_trading_date(year, month, day)


    h5_path = "/global/scratch/ryee/symbol_count/output/{year:04d}{month:02d}{day:02d}.h5".format(year=year, 
               month=month, day=day) 
    timing_path = "/global/scratch/ryee/symbol_count/timing/{year:04d}{month:02d}{day:02d}.txt".format(year=year, 
               month=month, day=day)     


    if not os.path.exists(h5_path):

        c = count_chunk_elements1(args.fname, max_chunk=max_chunk)

        # write the output file


        print(file_dt, ts, h5_path)
        write_h5_for_counter(c, ts, h5_path)


        print("total number of records", sum(c.values()))
        # for (i,(k,v)) in enumerate(islice(c.most_common(),100)):
        #     print ("\t".join([str(i), k.decode('utf-8').strip(), str(v)]))        

        t1 = time.time()
        print ("timing:", t0, t1, t1-t0)
        with open(timing_path, "w") as tfile:
            tfile.write("{0},{1},{2}".format(t0,t1,t1-t0))

    

