#!/bin/bash

for i in `ls slurm.out/*`; 
do 
	echo stats for $i
	grep "SparkDeploySchedulerBackend: Granted executor ID" $i|sed 's/.*hostPort//'
	tail -10 $i|grep "Job 0 finished" | sed 's/.*took/Time\ taken\:/'
	echo;echo
done
