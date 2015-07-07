#!/bin/bash
#SBATCH --job-name=taq_htc
#SBATCH --partition=savio
#SBATCH --account=co_dlab
#SBATCH --qos=dlab_normal
#SBATCH --ntasks=$1
#SBATCH --time=01:00:00
ht_helper.sh -t taq_htc.taskfile -n1 -dvk