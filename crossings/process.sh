#!/bin/bash

for i in `ls slurm.out/*`; 
do 
	echo stats for $i
	grep "SparkDeploySchedulerBackend: Granted executor ID" $i|sed 's/.*hostPort//'
	grep Stage.*finished $i|awk '{print $5, $6, $7, $12,$13}'
	tail -10 $i|grep Job.*finished | sed 's/.*took/Time\ taken\:/'
	echo;echo
done
