#!/bin/bash

# Helper script to submit spark jobs to sbatch parameterized by
# Number of nodes
# Amount of executor RAM
# Inifiniband flag

# Usage : submit.sh <Number of nodes> <RAM> <file> [-i]
# example : submit.sh 3 8G crossings.py -i

mkdir -p slurm.out
mkdir -p sbatch

cat << EOF >sbatch/sbatch.$$
#!/bin/bash
#SBATCH --job-name=spark-job
#SBATCH --partition=savio
#SBATCH --account=co_dlab
#SBATCH --qos=dlab_normal
#SBATCH --nodes=$1
#SBATCH --time=02:00:00

rm -rf /global/scratch/rsoni/testdata/crossings
rm -rf /global/scratch/rsoni/spark/*
# rm -rf /dev/shm/spark-*
source /global/home/users/rsoni/work/dlab-finance/spark_helper.sh
spark-start $4
spark-submit --master \$SPARK_URL --executor-memory $2 `pwd`/$3
spark-stop
EOF

cd slurm.out
echo sbatch ../sbatch/sbatch.$$
sbatch ../sbatch/sbatch.$$
