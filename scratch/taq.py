# Project : Dlab-Finance Processing TAQ data
# Desc : This is a test script to test reading and processing TAQ data with Spark

# TAQ record structure by list index
# 0 - Time in HHMMSSXXX
# 1 - Exchange Single char
# 2 - Symbol 16 char
# 3 - Sale condition
# 4 - Trade Volume
# 5 - Trade Price
# 6 - Trade Stop stock indicator
# 7 - Trade correction indicator
# 8 - Trade sequence number
# 9 - Source of trade
# 10 - Trade reporting facility
# 11 - Line change indicator
import sys
from random import random
from operator import add

from pyspark import SparkContext


if __name__ == "__main__":

    sc = SparkContext(appName="TAQProcessing")
    data = sc.textFile("/global/scratch/rsoni/testdata/taqtrade20100104")
    records = data.map(lambda s: [s[:9],s[9:10],s[10:26].strip(),s[26:30],int(s[30:39]),float(s[39:50])/10000.0,s[50:51],s[51:53],s[53:69],s[69:70],s[70:71],s[71:73]])
    saperec = records.filter(lambda rec: rec[2][:4]=='SAPE')
    print records.take(5)
    print records.count()
    

    print saperec.count()

    # This next line has trouble executing so commenting it out for now.
    for rec in saperec.take(5):
        print rec
