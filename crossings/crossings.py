# Project : Dlab-Finance Processing Quote data
# Desc : This job processes TAQ Quotes file and extracts number of crossings per second for NBB and NBO
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
outputDir="/global/scratch/rsoni/testdata/crossings/"
threshold=10

def crossings(list):
    # Calc avgbid
    NBBList = ([rec[1][3] for rec in list if rec[1][3] > 0])
    if NBBList != []:
        avgBid = sum(NBBList)/float(len(NBBList))
    else:
        avgBid = 0
    # Calc avg ask
    NBOList = ([rec[1][4] for rec in list if rec[1][4] < sys.maxsize])
    if NBOList != []:
        avgAsk = sum(NBOList)/float(len(NBOList))
    else:
        avgAsk = 0
    # Get Valid bids and offers
    bidList = [rec[1][1] for rec in list if rec[1][1] > 0]
    askList = [rec[1][2] for rec in list if rec[1][2] < sys.maxsize]
    crossBid=0
    if (len(bidList) > 0):
        currBid=bidList[0]<avgBid
        for i in range(len(bidList)):
            if currBid != bidList[i]<avgBid:
                crossBid = crossBid+1
                currBid = not(currBid)
    crossAsk=0
    if (len(askList) > 0):
        currAsk=askList[0]<avgAsk
        for i in range(len(askList)):
            if currAsk != askList[i]<avgAsk:
                crossAsk = crossAsk+1
                currAsk = not(currAsk)
    return (list[0][0],crossBid,crossAsk)

            
def processquote (record):
    # Sort by index created using zipWithIndex to preserve ordering in tied timestamps
    list1 = sorted(record[1])
    # Setup exchangeList for NBBO calculation
    exchangeList = ['A','B','C','D','I','J','K','M','N','T','P','S','Q','W','X','Y','Z']
    bidList = [0]*len(exchangeList)
    askList = [sys.maxsize]*len(exchangeList)
    nbbolist=[]
    crossingslist=[]
    idx=0
    currtime=0
    # Iterate over the list to calculate nbbo
    for i in range(len(list1)):
        if ((currtime != int(list1[i][1])) and (nbbolist != [])):
            if len(nbbolist) > threshold:
                (key,cbid,cask) = crossings(nbbolist)
                if ((cbid > threshold) or (cask > threshold)):
                    crossingslist.append((key,cbid,cask)) 
            #new second interval
            nbbolist=[]
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
    return crossingslist

if __name__ == "__main__":
    conf = SparkConf().setAppName("nbbo_hfalert")
    sc = SparkContext(conf=conf)
    data1 = sc.textFile(inputDir)
    data2 = data1.zipWithIndex()
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
