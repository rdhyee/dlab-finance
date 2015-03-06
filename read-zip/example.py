# I run this locally on my laptop using the following command:
#   spark-submit --jars hadoop-zip.jar example.py
#
# The `hadoop-zip.jar` file was built from the code at:
#   https://github.com/cotdp/com-cotdp-hadoop
#
# This example expects the `data/` directory to contain zip
# files with text files containing one record per line.

from pyspark import *

sc = SparkContext()

rdd = sc.newAPIHadoopFile(
        "data",
        "com.cotdp.hadoop.ZipFileInputFormat",
        "org.apache.hadoop.io.LongWritable",
        "org.apache.hadoop.io.Text")

def split_lines(text):
    return text.split()

print rdd.values().flatMap(split_lines).collect()
