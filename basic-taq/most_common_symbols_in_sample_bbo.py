#!/global/home/users/ryee/miniconda/envs/myenv3/bin/python

from glob import glob
from itertools import (islice, zip_longest)
from collections import Counter
from sys import argv
import time
import numpy as np

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


if __name__ == '__main__':

    t0 = time.time()

    faqname = "/global/scratch/aculich/mirror/EQY_US_ALL_BBO/EQY_US_ALL_BBO_2015/EQY_US_ALL_BBO_201501/EQY_US_ALL_BBO_20150102.zip"
    chunks = raw_taq.TAQ2Chunks(faqname,chunksize=1, process_chunk=False)
 
    try: 
        max_chunk = int(argv[1])
    except:
        max_chunk = None

    
    c = count_chunk_elements1(faqname, max_chunk=max_chunk)

    t1 = time.time()

    print("total number of records", sum(c.values()))

    print ("timing:", t0, t1, t1-t0)

    for (i,(k,v)) in enumerate(islice(c.most_common(),100)):
        print ("\t".join([str(i), k.decode('utf-8').strip(), str(v)]))

