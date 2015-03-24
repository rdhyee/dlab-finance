'''
Usage:  nbbo_hfa.py stock-ticker high-freq-threshold quote-file nbbo-dir
example: nbbo.py FB 30 hdfs://npatwa91.54310/w251/final/nbbo
If high-freq-threshold is not provided, 50 is default.
If stock-ticker is not provided, "AAPL" is default
If quote-file is not provided, "hdfs://npatwa91:54310/w251/final/taqquote20131218" is default.
If nbbo-dir is not provided, "hdfs://npatwa91.54310/w251/final/nbbo" is default

Output: nbbo  //NBBO (ms, (best-bid-price, best-ask-price)) HDFS file 
        nbbo_alerts.txt //alerts of HFT, unix file on driver
        nbbo_secsummary //per-second summary of avg best-bid, best-ask and #of crossings, unix file on driver

This program examines dailyquotes file for a particular stock,
finds best bid and best ask every milliseconds, generates an nbbo file in HDFS
It then finds average of best bid and best ask every second and then
finds #of times within each second the best bid and best ask crosses the average,
which is indicative of high-frequency trading. This count is compared against 
the threshold and the program prints the seconds during which the number of crossings 
exceed the threshold.



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
#spark-submit --master spark://npatwa91.softlayer.com:7077 --driver-memory 4G --executor-memory 4G nbbo_npatwa.py
#spark-submit --master spark://npatwa91.softlayer.com:7077 --conf spark.driver.memory=4G --conf spark.executor.memory=4G 

from pyspark import SparkContext, SparkConf

conf = SparkConf().setAppName("nbbo_hfalert")
#conf.set("spark.master", "spark://npatwa91.softlayer.com:7077")
#conf.set("spark.driver.memory", "4G")
#conf.set("spark.executor.memory", "4G")

sc = SparkContext(conf = conf)

# P Y S P A R K 
#pyspark --master spark://npatwa91.softlayer.com:7077 --driver-memory 4G --executor-memory 4G
#----------------------------------------------------------------------------------------------------

import sys

#defaults

stock = "AAPL"
HFTH = 50
quotefile = "hdfs://npatwa91:54310/w251/final/taqquote20131218"
nbbo_dir = "hdfs://npatwa91:54310/w251/final/nbbo"

if (len(sys.argv) == 5):
    stock = str(sys.argv[1])
    HFTH = int(sys.argv[2])
    quotefile = str(sys.argv[3]) 
    nbbo_dir = str(sys.argv[4]) 
if (len(sys.argv) == 4):
    stock = str(sys.argv[1])
    HFTH = int(sys.argv[2])
    quotefile == str(sys.argv[3]) 
if (len(sys.argv) == 3): 
    stock = str(sys.argv[1])
    HFTH = int(sys.argv[2])
elif (len(sys.argv) == 2):
    stock = str(sys.argv[1])
else:
    print ("Using defaults for arguments.\n")

nbbo_dir = nbbo_dir + "/" + stock
alerts_file = "nbbo_alerts"+stock+".txt"
summary_file = "nbbo_sec"+stock+".txt"

def crossings_cnt(mytuple):
    #mytuple: ([(ms1, p1), (ms2, p2)..], avg)
    avg = mytuple[1]
    mylist = mytuple[0]
    edgecnt = 0
    direction = 2 # undefined
    mylistsorted = sorted(mylist, key=lambda rec: rec[0])
    for i in range(len(mylistsorted)):
        price = mylist[i] [1]
        if (price > avg):
            newdir = 1   # upper half
        else:
            newdir = 0   # lower half
        if (direction != 2) and (newdir != direction):
            edgecnt = edgecnt + 1
        direction = newdir
    return(edgecnt)



RDD = sc.textFile(quotefile)

stockRDD = RDD.filter(lambda line: stock in line)
records = stockRDD.map(lambda line: [line[0:9], line[9], line[10:26].strip(), float(line[26:37])/10000, int(line[37:44]), float(line[44:55])/10000, int(line[55:62]), line[62]])
# find records for the given stock
apple = records.filter(lambda rec: stock in rec[2])

# create k-v for exchange etc for examining data
#appleexch = apple.map(lambda rec: (rec[1], rec)) # key is the exchange
#applesec = apple.map(lambda rec: (rec[0] [0:6], rec)) # key is time in seconds
#applecond = apple.map(lambda rec: (rec[7], rec)) # key is the condition
#appleexch.countByKey()

# create k-v with millisecond as the key and bid or ask as value
bid = apple.map(lambda rec: (rec[0], rec[3]))
ask = apple.map(lambda rec: (rec[0], rec[5]))

# find max bid and min ask for every milli second - they are best bid and best ask
bestbid = bid.reduceByKey(max)  #format: key=millisecond value=max-price
bestask = ask.reduceByKey(min)  #format: key=millisecond, value=min-price
nbbo = bestbid.join(bestask)   #format: key=millisecond, value=(max-bid, min-ask)

nbbo.saveAsTextFile(nbbo_dir)


# find average values over a second of best bid and best ask
bbsec = bestbid.map(lambda rec: (rec[0] [0:6], rec[1]))  #key=sec, value=min-price
bbsecagg = bbsec.mapValues(lambda x: (x, 1)).reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))  #append count and then total
bbsecavg = bbsecagg.map(lambda rec: (rec[0], (rec[1] [0])/(rec[1] [1])))

basec = bestask.map(lambda rec: (rec[0] [0:6], rec[1]))
basecagg = basec.mapValues(lambda x: (x, 1)).reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1]))
basecavg = basecagg.map(lambda rec: (rec[0], (rec[1] [0])/(rec[1] [1])))

# go back to bestbid millisecond and create a second key, but maintain millisecond value
# IMPORTANT: create a list object with tuple inside to allow + operator in reduce function to work

bestbidsec = bestbid.map(lambda rec: (rec[0] [0:6], [(rec[0], rec[1])]))  #key=second, value = (ms, value)
bestasksec = bestask.map(lambda rec: (rec[0] [0:6], [(rec[0], rec[1])]))
bestbidlist = bestbidsec.reduceByKey(lambda x, y: x + y)   #list addition, this will fuse the records
#bestbidlist = bestbidsec.reduceByKey(lambda x, y: [x[0] + y[0], x[1] + y[1]])   #list addition, this will fuse the records
bestasklist = bestasksec.reduceByKey(lambda x, y: x + y)

# join so that you get (sec, (best ms, secavg)) 
bbjoin = bestbidlist.join(bbsecavg)  # key=second, value = ([(ms1, value1), (ms2, value2), (ms3, value3)], avg)
bajoin = bestasklist.join(basecavg)

#groupBy is going to collect all values of a key and send them to one node.
#     Spark does not recommend using it, but often one needs sorted value list to operate on.
#     crossingscnt is that task
#reduceBy/aggregateBy is going to do combining at the source node and then send results to one node. 
#     Above works well for aggregate functions that can be done in parallel, e.g. count, min, max
#combineByKey is more general function. 
#createCombiner
#mergeValue
#mergeCombiner

# find number of times each second the best bid and best ask crosses the average
bbfreq = bbjoin.mapValues(crossings_cnt) # value = #of crossings
bafreq = bajoin.mapValues(crossings_cnt)

# filter seconds where crossings_count exceed the threshold 
bbfreqgth = bbfreq.filter(lambda rec: rec[1] > HFTH).sortByKey().collect()
bafreqgth = bafreq.filter(lambda rec: rec[1] > HFTH).sortByKey().collect()

fp = open(alerts_file, 'w')
print >>fp, "Best Buy High Frequency Alerts\n"
for i in range(len(bbfreqgth)):
    localkey = bbfreqgth[i] [0]
    localfreq = bbfreqgth[i] [1]
    localvalues = bbjoin.lookup(localkey)[0]  # get a tuple ([(ms, price), (ms, price), ...], avg)
    localavg = localvalues[1]
    locallist = sorted(localvalues[0], key=lambda rec: rec[0])
    print >>fp, "Second:", localkey, "avg price:", format(localavg, '0.3f'), "#of crossings:", localfreq
    print >>fp, '\t', "millisecond", '\t', "price"
    for j in range(len(locallist)):
        print >>fp, '\t', locallist[j] [0], '\t', format(locallist[j] [1], '0.3f') 

print >>fp, "\nBest Ask High Frequency Alerts\n"

for i in range(len(bafreqgth)):
    localkey = bafreqgth[i] [0]
    localfreq = bafreqgth[i] [1]
    localvalues = bajoin.lookup(localkey)[0]  # get a tuple ([(ms, price), (ms, price), ...], avg)
    localavg = localvalues[1]
    locallist = sorted(localvalues[0], key=lambda rec: rec[0])
    print >>fp, "Second: ", localkey, "avg price: ", localavg, "#of crossings: ", localfreq
    print >>fp, '\t', "millisecond", '\t', "price"
    for j in range(len(locallist)):
        print >>fp, '\t', locallist[j] [0], '\t', format(locallist[j] [1], '0.3f') 

fp.close()

#if collect was not used, this can be used
#bbfreqgth.saveAsTextFile("hdfs://npatwa91:54310/w251/final/bbfreqgth")
#bafreqgth.saveAsTextFile("hdfs://npatwa91:54310/w251/final/bafreqgth")


# create a per-second record of NBBO and #of crossings around average

nbbofreq = bbfreq.join(bafreq) # create a value tuple tuple (#of crossings best-bid, #of crossings best-ask)
nbboavg  = bbsecavg.join(basecavg)   # average per second of best bid and best ask
nbbosec = nbboavg.join(nbbofreq) # create a tuple of ((avg-best-bid, avg-best-ask), (#of crossings best-bid, #of crossings best-ask))
nbbosec = nbbosec.sortByKey() # created sorted list
nbbo_secsummary = nbbosec.collect()

fp = open(summary_file, 'w')
print >>fp, "(second, ((avg best buy, avg best ask), (#crossings best buy, #crossings best ask)))\n"
for i in range(len(nbbo_secsummary)):
#    nbbo_secsummary[i] [1] [0] [0] = format(nbbo_secsummary[i] [1] [0] [0], '0.3f')
#    nbbo_secsummary[i] [1] [0] [1] = format(nbbo_secsummary[i] [1] [0] [1], '0.3f')
    print >>fp, nbbo_secsummary[i] 

fp.close()

#if collect was not used, this an be used
#nbbosec.saveAsTextFile("hdfs://npatwa91:54310/w251/final/nbbosec_avg_freq")

