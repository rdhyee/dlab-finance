# Project : Dlab-Finance 
# W251 Nital Patwa and Ritesh Soni
# Program name: acc.py
# Desc : This program processes TAQ Quotes file to detect high-velocity price movement.
# Any change in national best bid or ask price of more than 5% in a second is flagged and recorded.
# By aggregating such events over 10-minute interval we can measure volatality and liquidity.
# Usage Instructions:
# Change inputDir to specify daily quote file and outputDir to specify where events will be reported.
# Change threshold from default of 0.05 if required
# ./submit.sh 4 8G acc.py
#             ^Number of Nodes
 
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

inputDir = "/global/scratch/npatwa/sparkinput/taqquote20100505"
outputDir = "/global/scratch/npatwa/sparkoutput/cacc20100505/"
threshold=0.05

def secavg(list):
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
    return (list[0][0],avgBid,avgAsk)

            
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
    currbid = 0
    currask = 0
    currkey = (0,0)
    # Iterate over the list to calculate nbbo
    for i in range(len(list1)):
        newtime = int(list1[i][1])
        if ((newtime  >= 93000) and (newtime <= 160000)):
            if ((currtime != newtime) and (nbbolist != [])):
                (key,cbid,cask) = secavg(nbbolist)
                if ((currbid > 0) and (currask > 0) and (cbid > 0) and (cask > 0)):
                    if (((abs(cbid-currbid))/currbid > threshold) or ((abs(cask-currask))/currask > threshold)):
                        crossingslist.append((currkey,currbid,currask)) 
                        crossingslist.append((key,cbid,cask)) 
                #new second interval
                nbbolist=[]
                idx=0
                currtime= newtime
                currkey = key
                currbid = cbid
                currask = cask
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
                    nbbolist.append(((record[0],list1[i][1]),(idx,list1[i][2],list1[i][4],max(bidList),min(askList))))
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
    result = data3.flatMap(lambda records: processquote(records)).map(lambda rec: [rec[0][0],rec[0][1],rec[1],rec[2]])
    result.saveAsTextFile(outputDir)
