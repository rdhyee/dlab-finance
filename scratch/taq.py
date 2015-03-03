import sys
from random import random
from operator import add

from pyspark import SparkContext


if __name__ == "__main__":

    sc = SparkContext(appName="TAQProcessing")
    data = sc.textFile("/global/scratch/rsoni/testdata/taqtrade20100104")
    records = data.map(lambda s: [s[:9],s[9:10],s[10:26],s[26:30],s[30:39],s[39:50],s[50:51],s[51:53],s[53:69],s[69:70],s[70:71],s[71:73]])
    saperec = records.filter(lambda rec: rec[2]=='SAPE  ')
    # print records.take(5)
    print records.count()
    print saperec.count()
