#!/bin/bash
#SBATCH --job-name=spark-job
#SBATCH --partition=savio
#SBATCH --account=ac_dlab
#SBATCH --qos=condo_dlab
#SBATCH --nodes=3
#SBATCH --time=02:00:00

source /global/home/groups/allhands/bin/spark_helper.sh
spark-start
spark-submit --master $SPARK_URL --executor-memory 8G --conf "spark.local.dir=/global/home/users/rsoni/tmp" /global/home/users/rsoni/work/dlab-finance/nbbo/nbbo.py
spark-stop
