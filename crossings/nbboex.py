# Project : Dlab-Finance
# W251 Nital Patwa and Ritesh Soni
# Desc : This program counts for each exchange, the #of times it produced best bid (or ask) and average size of bid (or ask)
# The purpose is to understand what roles exchanges such as BATS play.
# Usage Instructions
# Change inputDir for daily quote file and outputDir for location of output
# ./submit.sh 4 8G nbboex.py
#             ^#of nodes


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

inputDir="/global/scratch/npatwa/sparkinput/taqquote20100505"
outputDir="/global/scratch/npatwa/sparkoutput/nbboexsize20100505/"

            
def processquote (record):
    # Sort by index created using zipWithIndex to preserve ordering in tied timestamps
    listOrig = sorted(record[1])
    list1 = [rec for rec in listOrig if ((int(rec[1]) >= 93000000) and (int(rec[1]) <= 160000000))]  # filter the list for regular stock hours 
    # Setup exchangeList for NBBO calculation
    exchangeList = ['A','B','C','D','I','J','K','M','N','T','P','S','Q','W','X','Y','Z']
    bidList = [0]*len(exchangeList)
    bidSize = [0]*len(exchangeList)
    askList = [sys.maxsize]*len(exchangeList)
    askSize = [0]*len(exchangeList)
    nbboList=[]
    bbExCnt = [0]*len(exchangeList)
    baExCnt = [0]*len(exchangeList)
    bbExSize = [0]*len(exchangeList)
    baExSize = [0]*len(exchangeList)
    currtime=0
    # Iterate over the list to calculate nbbo
    for i in range(len(list1)):
        if (currtime != int(list1[i][1])): # change of millisecond
            # Find NBBO and exchange count
            if (max(bidList) > 0) or (min(askList) < sys.maxsize):
                # Output key Value pairs where
                # Key : (<Stock Ticker>, <Time in ms seconds>)
                # Value : (<best-bid>,<best-bid-exchange>,<best-bid-size>, <best-ask>,<best-ask-exchange>,<best-ask-size> )
                maxbid = max(bidList)
                minask = min(askList)
                bbEx = bidList.index(maxbid)  #index of exchange showing max bid
                baEx = askList.index(minask)  #index of exchange showing min ask
                bbSize = bidSize[bbEx]    #size
                baSize = askSize[baEx]    #size
                bbExCnt[bbEx] += 1
                baExCnt[baEx] += 1
                bbExSize[bbEx] += bbSize
                baExSize[bbEx] += baSize
             
            currtime=int(list1[i][1])

        # set the latest bid and ask if bid & ask are not zero and if bidsize and asksize are not zero
        # Backout the bid or ask if either is 0
        if ((list1[i][2] != 0) & (list1[i][3] != 0)):
            bidList[exchangeList.index(list1[i][6])] = list1[i][2]
            bidSize[exchangeList.index(list1[i][6])] = list1[i][3]
        elif ((list1[i][2] == 0) or (list1[i][8] == 'B')):
            bidList[exchangeList.index(list1[i][6])] = 0
            bidSize[exchangeList.index(list1[i][6])] = 0 # size

        if ((list1[i][4] != 0) & (list1[i][5] != 0)):
            askList[exchangeList.index(list1[i][7])] = list1[i][4]
            askSize[exchangeList.index(list1[i][7])] = list1[i][5]
        elif ((list1[i][4] == 0) or (list1[i][8] == 'B')):
            askList[exchangeList.index(list1[i][7])] = sys.maxsize
            askSize[exchangeList.index(list1[i][7])] = 0
    
    for j in range(len(exchangeList)):
        if (bbExCnt[j] > 0): 
            bbExSize[j] = bbExSize[j]/bbExCnt[j]
        if (baExCnt[j] > 0):
            baExSize[j] = baExSize[j]/baExCnt[j]
    nbboList.append((record[0],(bbExCnt, bbExSize, baExCnt, baExSize)))

    return nbboList

if __name__ == "__main__":
    conf = SparkConf().setAppName("nbbo_hfalert")
    sc = SparkContext(conf=conf)
    data1 = sc.textFile(inputDir)
    data2 = data1.zipWithIndex()
    data3 = data2.map(lambda rec: (rec[0][10:26].strip(), 
                                   (rec[1],  #index
                                    rec[0][0:9], #ms time
                                    float(rec[0][26:37])/10000, #bid price
                                    int(rec[0][37:44]), #bid size
                                    float(rec[0][44:55])/10000, #ask price
                                    int(rec[0][55:62]), #ask size
                                    rec[0][67], #bid exchange
                                    rec[0][68],  #ask exchange
                                    rec[0][87]))).groupByKey()  #cancel or correction
    result = data3.flatMap(lambda records: processquote(records)).map(lambda rec: [rec[0], rec[1][0], rec[1][1], rec[1][2], rec[1][3]])
    result.saveAsTextFile(outputDir)
