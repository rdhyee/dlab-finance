#!/bin/bash

CURRDIR=$PWD

source /global/home/groups/allhands/bin/spark_helper.sh
spark-start
spark-submit --master $SPARK_URL $CURRDIR/$1
spark-stop
