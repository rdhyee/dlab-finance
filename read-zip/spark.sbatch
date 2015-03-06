#!/bin/bash
#SBATCH --job-name=hadoop_zip
#SBATCH --partition=savio
#SBATCH --account=ac_dlab
#SBATCH --qos=nc_debug
#SBATCH --nodes=4
#SBATCH --time=00:10:00

source /global/home/groups/allhands/bin/spark_helper.sh

# Start Hadoop On Demand
spark-start

# Example 1
# spark-submit --master $SPARK_URL $SPARK_DIR/examples/src/main/python/pi.py

# Example 2
# spark-submit --master $SPARK_URL $SPARK_DIR/examples/src/main/python/wordcount.py /foo/bar

# Stop Hadoop On Demand
spark-stop
