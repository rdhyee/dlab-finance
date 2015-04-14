# Project : Dlab-Finance Processing Quote data
# Desc : This is a test script to test reading and processing Quote data with Spark
'''
fields of dailyquotes file taqquote
[0:8]HHMMSSXXX
[9] text EXCHANGE N Nyse  T/Q NASDAQ
[10:25] text symbol 6+10
[26:36] bid price 7+4
[37:43] bid size (units)
[44:54] ask price 7+4
[55:61] ask size
[62] text Condition of quote
[63:66] market maker
[67] bid exchange
[68] ask aexchange
[69:84] int seqno
[85] int bbo indicator
[86] int NASDAQ BBO indocator
[87] text cancel/correction
[88] text C=CTA N=UTP
[90] text Retail interest indicator
[...]
'''

import sys
from random import random
from operator import add

from pyspark import SparkContext, SparkConf

inputDir="/global/scratch/rsoni/testdata/quoteplain/"
outputDir="/global/scratch/rsoni/testdata/nbbo/"

def processquote (record):
    # Sort by timestamp in millisecond
    list1 = sorted(record[1],key=lambda rec: rec[0])
    
    # Filter out bid/asks with value 0 or size 0 DO NOT FILTER HERE
    # list1 = [v for v in sortlist if (v[3] != 0) & (v[4] != 0) & (v[5] != 0) & (v[6] != 0)]

    # Setup exchangeList for NBBO calculation
    exchangeList = ['A','B','C','D','I','J','K','M','N','T','P','S','Q','W','X','Y','Z']
    bidList = [0]*len(exchangeList)
    askList = [sys.maxsize]*len(exchangeList)
    nbbolist=[]
    # Iterate over the list to calculate nbbo
    for i in range(len(list1)):
        # set the latest bid and ask if bid & ask are not zero and if bidsize and asksize are not zero
        # Backout the bid or ask if either is 0
        if ((list1[i][3] != 0) & (list1[i][4] != 0)):
            bidList[exchangeList.index(list1[i][8])] = list1[i][3]
        elif (list1[i][3] == 0):
            bidList[exchangeList.index(list1[i][8])] = 0

        if ((list1[i][5] != 0) & (list1[i][6] != 0)):
            askList[exchangeList.index(list1[i][9])] = list1[i][5]
        elif (list1[i][5] == 0):
            askList[exchangeList.index(list1[i][9])] = sys.maxsize

        # calculate NBBO
        nbbolist.append((record[0],list1[i][0],max(bidList),min(askList)))
    return nbbolist

if __name__ == "__main__":
    conf = SparkConf().setAppName("nbbo_hfalert")
    sc = SparkContext(conf=conf)
    data = sc.textFile(inputDir)
    # data1 = data.filter(lambda line: line[10:26].strip() == 'AAPL')
    biddata = data.map(lambda line: (line[10:26].strip(), 
                                     (int(line[0:9]), 
                                      int(line[0:6]), 
                                      int(line[6:9]), 
                                      float(line[26:37])/10000,
                                      int(line[37:44]),
                                      float(line[44:55])/10000,
                                      int(line[55:62]),
                                      line[9],
                                      line[67],
                                      line[68]))).groupByKey()
    result = biddata.flatMap(lambda rec: processquote(rec))
    result.saveAsTextFile(outputDir)
