#!/bin/bash

# Python job script

# Job name:
#SBATCH --job-name=raw_taq_local
#
# Partition:
#SBATCH --partition=savio
#
# Account:
#SBATCH --account=co_dlab
#
# QOS:
#SBATCH --qos=dlab_normal
#
## Run command
python run.py