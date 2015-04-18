#!/bin/bash

# Helper script to submit spark jobs to sbatch parameterized by
# Number of nodes
# Amount of executor RAM
# Inifiniband flag

# Usage : submit.sh <Number of nodes> <RAM> [-i]
# example : submit.sh 3 8G

cat << EOF >sbatch/nbbo.sbatch.$$
#!/bin/bash
#SBATCH --job-name=spark-job
#SBATCH --partition=savio
#SBATCH --account=co_dlab
#SBATCH --qos=dlab_normal
#SBATCH --nodes=$1
#SBATCH --time=02:00:00

rm -rf /global/scratch/rsoni/testdata/nbbo
# rm -rf /global/scratch/rsoni/spark/*
rm -rf /dev/shm/spark-*
source /global/home/users/rsoni/work/dlab-finance/spark_helper.sh
spark-start $3
spark-submit --master \$SPARK_URL --executor-memory $2 /global/home/users/rsoni/work/dlab-finance/nbbo/nbbo.py
spark-stop
EOF

cd slurm.out
sbatch ../sbatch/nbbo.sbatch.$$
