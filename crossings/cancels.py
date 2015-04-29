# Project : Dlab-Finance Processing Quote data
# Desc : This job processes TAQ Quotes file to detect cancelled bids and asks 
# 
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
[87] text cancel/correction  A=Normal B=Cancel C=Corrected-price
[88] text C=CTA N=UTP
[90] text Retail interest indicator
[...]
'''

import sys
from random import random
from operator import add

from pyspark import SparkContext, SparkConf

inputDir="/global/scratch/npatwa/sparkinput/taqquote20100506"
outputDir="/global/scratch/npatwa/sparkoutput/cancels20100506/"
threshold=5

            
def processquote (record):
    # Sort by index created using zipWithIndex to preserve ordering in tied timestamps
    list1 = sorted(record[1])
    # Setup exchangeList for NBBO calculation
    exchangeList = ['A','B','C','D','I','J','K','M','N','T','P','S','Q','W','X','Y','Z']
    cancelExCnt = [0]*len(exchangeList)
    currtime=0
    outList = []
    errCnt = 0
    # Iterate over the list to calculate cancellations
    for i in range(len(list1)):
        if ((currtime != int(list1[i][1])) and (sum(cancelExCnt) != 0)): # change of second
            # check cancellation count
            if ((sum(cancelExCnt) >= threshold) or (errCnt > 0)):
                # Output key Value pairs where
                # Key : (<Stock Ticker>, <Time in seconds>)
                # Value : cancellationlist
                outList.append(((record[0],list1[i][1]),(cancelExCnt, errCnt)))
            cancelExCnt = [0]*len(exchangeList)
            errCnt = 0
            currtime=int(list1[i][1])
        if (list1[i] [8] == 'B') :
            cancelExCnt[exchangeList.index(list1[i] [6])] += 1
        if (list1[i] [6] != list1[i] [7]):
            errCnt += 1
        
    return outList

if __name__ == "__main__":
    conf = SparkConf().setAppName("nbbo_hfalert")
    sc = SparkContext(conf=conf)
    data1 = sc.textFile(inputDir)
    data2 = data1.zipWithIndex()
    data3 = data2.map(lambda rec: (rec[0][10:26].strip(), 
                                   (rec[1],  #index
                                    rec[0][0:6], #sec time 6 ms time 9   1
                                    float(rec[0][26:37])/10000, #bid price  2
                                    int(rec[0][37:44]), #bid size 3
                                    float(rec[0][44:55])/10000, #ask price 4
                                    int(rec[0][55:62]), #ask size 5
                                    rec[0][67], #bid exchange 6
                                    rec[0][68],  #ask exchange 7
                                    rec[0][87]))).groupByKey()  #cancel or correction 8
    result = data3.flatMap(lambda records: processquote(records)).map(lambda rec: [rec[0][0],rec[0][1],rec[1][0],rec[1][1]])
    result.saveAsTextFile(outputDir)
