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
    # Sort by index created using zipWithIndex to preserve ordering in tied timestamps
    list1 = sorted(record[1])
    # Setup exchangeList for NBBO calculation
    exchangeList = ['A','B','C','D','I','J','K','M','N','T','P','S','Q','W','X','Y','Z']
    bidList = [0]*len(exchangeList)
    askList = [sys.maxsize]*len(exchangeList)
    nbbolist=[]
    idx=0
    currtime=0
    # Iterate over the list to calculate nbbo
    for i in range(len(list1)):
        if(currtime != int(list1[i][1])):
            #new second interval
            idx=0
            currtime=int(list1[i][1])
        else:
            idx=idx+1
        # set the latest bid and ask if bid & ask are not zero and if bidsize and asksize are not zero
        # Backout the bid or ask if either is 0
        if ((list1[i][2] != 0) & (list1[i][3] != 0)):
            bidList[exchangeList.index(list1[i][6])] = list1[i][2]
        elif ((list1[i][2] == 0) or (list1[i][8] == 'B')):
            bidList[exchangeList.index(list1[i][6])] = 0
        if ((list1[i][4] != 0) & (list1[i][5] != 0)):
            askList[exchangeList.index(list1[i][7])] = list1[i][4]
        elif ((list1[i][4] == 0) or (list1[i][8] == 'B')):
            askList[exchangeList.index(list1[i][7])] = sys.maxsize
        # calculate NBBO
        if (max(bidList) > 0) or (min(askList) < sys.maxsize):
            # Output key Value pairs where
            # Key : (<Stock Ticker>, <Time in seconds>)
            # Value : (<record-index>,<bid-price>,<ask-price>,<best-bid>,<best-ask>)
            nbbolist.append((record[0]+'\t'+list1[i][1],(idx,list1[i][2],list1[i][4],max(bidList),min(askList))))
    return nbbolist

if __name__ == "__main__":
    conf = SparkConf().setAppName("nbbo_hfalert")
    sc = SparkContext(conf=conf)
    data1 = sc.textFile(inputDir)
    data2 = data1.zipWithIndex()
    # data1 = data.filter(lambda line: line[10:26].strip() == 'AAPL')
    # data3 = data2.map(lambda rec: (rec[0][10:26].strip(), 
    #                                (rec[1],
    #                                 int(rec[0][0:9]), 
    #                                 int(rec[0][0:6]), 
    #                                 int(rec[0][6:9]), 
    #                                 float(rec[0][26:37])/10000,
    #                                 int(rec[0][37:44]),
    #                                 float(rec[0][44:55])/10000,
    #                                 int(rec[0][55:62]),
    #                                 rec[0][9],
    #                                 rec[0][67],
    #                                 rec[0][68],
    #                                 rec[0][87]))).groupByKey()
    data3 = data2.map(lambda rec: (rec[0][10:26].strip(), 
                                   (rec[1],
                                    rec[0][0:6], 
                                    float(rec[0][26:37])/10000,
                                    int(rec[0][37:44]),
                                    float(rec[0][44:55])/10000,
                                    int(rec[0][55:62]),
                                    rec[0][67],
                                    rec[0][68],
                                    rec[0][87]))).groupByKey()
    result = data3.flatMap(lambda records: processquote(records))
    result.saveAsTextFile(outputDir)
