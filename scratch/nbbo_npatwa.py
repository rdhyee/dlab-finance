'''
This program examines dailyquotes file for a particular stock,
finds best bid and best ask every milliseconds, prints nbbo tuple.
It then finds average of best bid and best ask every second.
Lastly it finds #of times within each second the best bid and best ask crosses the average,
which is indicative of high-frequency trading

REF:
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
from pyspark import *

sc = SparkContext()


def edgedtct(mylist):
    edgecnt = 0
    dir = 2
    mylist.sort(key=lambda tup: tup[0] [0])
    avg = mylist[0] [1]
    for i in range(len(mylist)):
        price = mylist[i] [0] [1]
        if (price > avg):
            newdir = 1
        else:
            newdir = 0
        if (dir != 2) and (newdir != dir):
            edgecnt = edgecnt + 1
        dir = newdir
    return(edgecnt)


RDD = sc.textFile("hdfs://npatwa91:54310/w251/final/taqquote20131218")
stockRDD = RDD.filter(lambda line: 'AAPL' in line)
records = stockRDD.map(lambda line: [line[0:9], line[9], line[10:26].strip(), float(line[26:37])/10000, int(line[37:44]), float(line[44:55])/10000, int(line[55:62]), line[62]])
# find records for the given stock
apple = records.filter(lambda rec: 'AAPL' in rec[2])

# create k-v for exchange etc for examining data
#appleexch = apple.map(lambda rec: (rec[1], rec)) # key is the exchange
#applesec = apple.map(lambda rec: (rec[0] [0:6], rec)) # key is time in seconds
#applecond = apple.map(lambda rec: (rec[7], rec)) # key is the condition
#appleexch.countByKey()

# create k-v with millisecond as the key and bid or ask as value
bid = apple.map(lambda rec: (rec[0], rec[3]))
ask = apple.map(lambda rec: (rec[0], rec[5]))

# find max bid and min ask for every milli second - they are best bid and best ask
bestbid = bid.reduceByKey(max)
#bestbid = bestbid.sortByKey()

bestask = ask.reduceByKey(min)
#bestask = bestask.sortByKey()
nbbo = bestbid.join(bestask)
print nbbo.take(10)# nbbo was no longer sorted.

# find average values over a second of best bid and best ask
bbsec = bestbid.map(lambda rec: (rec[0] [0:6], rec[1]))  #bbsec is loosing millisecond value
#bbsec = bbsec.sortByKey()
bbsecagg = bbsec.mapValues(lambda x: (x, 1)).reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))
bbsecavg = bbsecagg.map(lambda rec: (rec[0], (rec[1] [0])/(rec[1] [1])))
#bbsecavg = bbsecavg.sortByKey()

basec = bestask.map(lambda rec: (rec[0] [0:6], rec[1]))
#bbsec = basec.sortByKey()
basecagg = basec.mapValues(lambda x: (x, 1)).reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))
basecavg = basecagg.map(lambda rec: (rec[0], (rec[1] [0])/(rec[1] [1])))
#basecavg = basecsvg.sortByKey()

# find number of times each second the best bid and best ask crosses the average
# bbsec is a list every second, bbsecavg is bestbid average every second
# produce bbcross which is (second, #of bb crossings)

# join so that you get (sec, (best ms, secavg)) 
bestbidsec = bestbid.map(lambda rec: (rec[0] [0:6], rec))  #key=second, value = (ms, value)
bestasksec = bestask.map(lambda rec: (rec[0] [0:6], rec))

bbjoin = bestbidsec.join(bbsecavg)  # key=second, value = ((ms, value), avg)
bajoin = bestasksec.join(basecavg)

bblist = bbjoin.groupByKey() # key=second, value = list [((ms, value), avg), ((ms, value), avg)]
balist = bajoin.groupByKey()
bbfreq = bblist.mapValues(edgedtct) # value = #of edges
bafreq = balist.mapValues(edgedtct)

nbbofreq = bbfreq.join(bafreq)

nbbofinal = nbbo.join(nbbofreq)
nbbofinal = nbbofinal.sortByKey()

nbbofinal.saveAsTextFile("hdfs://npatwa91:54310/w251/final/nbbofinal.txt")
