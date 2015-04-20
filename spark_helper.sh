#!/bin/bash
#
# Copyright (c) 2014-2015, Yong Qin <yong.qin@lbl.gov>. All rights reserved.
#
# This script provides a set of shell functions to help to set up a Spark On 
# Demand (SOD) environment with Lustre or other POSIX compliant shared file 
# system within a given SLURM allocation.
#
# Usage:
#
#     source spark_helper.sh
#
#     echo Start Spark On Demand
#     spark-start
#
#     echo Example 1
#     spark-submit --master $SPARK_URL $SPARK_DIR/examples/src/main/python/pi.py
#
#     echo Example 2
#     spark-submit --master $SPARK_URL $SPARK_DIR/examples/src/main/python/wordcount.py input
#
#     echo Stop Spark On Demand
#     spark-stop
#


# GLOBAL settings
# Lustre SCRATCH file system
SCRATCH=${SCRATCH:-"/global/scratch/$USER"}
SPARK_IPOIB=0
SPARK_WORK_DIR=
SPARK_MASTER_IP=
SPARK_WORKER_DIR=
SPARK_CONF_DIR=
SPARK_LOG_DIR=
SPARK_LOCAL_DIRS=
SPARK_URL=


# GLOBAL functions
function ERROR () {
    local RETVALUE="$1"
    local RETSTRING="$2"
    echo "`date +"%b %d %H:%M:%S"` ERROR: "$RETSTRING"" >&2
    exit "$RETVALUE"
}


function WARNING () {
    local RETSTRING="$1"
    echo "`date +"%b %d %H:%M:%S"` WARNING: "$RETSTRING"" >&2
}


function INFO () {
    local RETSTRING="$1"
    if [[ $VERBOSE -eq 1 ]]; then
        echo "`date +"%b %d %H:%M:%S"` INFO: "$RETSTRING"" >&2
    fi
}


function spark-init() {
    # processing command line options
    while true; do
        case "$1" in
            -i)
                SPARK_IPOIB=1
                shift
                ;;
            --)
                shift
                break
                ;;
            *)
                break
                ;;
        esac
    done

    # verify if we are in a SLURM allocation or not
    if  [[ -z $SLURM_JOB_ID ]]; then
        WARNING "Valid SLURM allocation not found. Spark initialization aborted!"
        return
    fi

    # load spark module
    module -t list 2>&1 | grep ^spark >/dev/null
    if [[ $? -ne 0 ]]; then
        module load java spark >/dev/null 2>&1
    fi

    # initialize spark WORK, CONF, LOG, LOCAL and TMP dirs
    SPARK_WORK_DIR=${SCRATCH}/spark/${SLURM_JOB_NAME##*/}.${SLURM_JOB_ID}

    if [[ $SPARK_IPOIB == 0 ]]; then
        SPARK_MASTER_IP=${SLURMD_NODENAME}
    else
        SPARK_MASTER_IP=ib-${SLURMD_NODENAME}
    fi

    SPARK_WORKER_DIR=${SPARK_WORK_DIR}
    SPARK_CONF_DIR=${SPARK_WORK_DIR}/conf
    SPARK_LOG_DIR=${SPARK_WORK_DIR}/log
    SPARK_LOCAL_DIRS=${SPARK_WORK_DIR}/tmp
    # SPARK_LOCAL_DIRS=/dev/shm
    export SPARK_WORK_DIR SPARK_MASTER_IP SPARK_WORKER_DIR SPARK_CONF_DIR SPARK_LOG_DIR SPARK_LOCAL_DIRS

    # create WORK and CONF dirs, and switch to the WORK dir
    mkdir -p $SPARK_CONF_DIR
    cd $SPARK_WORK_DIR

    # copy initial config files from spark default config directory
    cp $SPARK_DIR/conf/spark-env.sh.template $SPARK_CONF_DIR/spark-env.sh

    # prepare slave hostfile
    if [[ $SPARK_IPOIB == 0 ]]; then
        echo $SLURM_NODELIST | sed -e $'s/,/\\\n/g' > $SPARK_CONF_DIR/slaves
    else
        echo $SLURM_NODELIST | sed -e $'s/,/\\\n/g' | sed -e $'s/^/ib-/g' > $SPARK_CONF_DIR/slaves
    fi

    # spark-env.sh
    echo "" >> $SPARK_CONF_DIR/spark-env.sh
    echo "# Overwrite environment variable JAVA_HOME" >> $SPARK_CONF_DIR/spark-env.sh
    echo "export JAVA_HOME=$JAVA_HOME" >> $SPARK_CONF_DIR/spark-env.sh
    echo "" >> $SPARK_CONF_DIR/spark-env.sh
    echo "# Overwrite location of the worker directory" >> $SPARK_CONF_DIR/spark-env.sh
    echo "export SPARK_WORKER_DIR=$SPARK_WORKER_DIR" >> $SPARK_CONF_DIR/spark-env.sh
    echo "" >> $SPARK_CONF_DIR/spark-env.sh
    echo "# Overwrite location of the log directory" >> $SPARK_CONF_DIR/spark-env.sh
    echo "export SPARK_LOG_DIR=$SPARK_LOG_DIR" >> $SPARK_CONF_DIR/spark-env.sh
    echo "" >> $SPARK_CONF_DIR/spark-env.sh
    echo "# Overwrite location of the local directory" >> $SPARK_CONF_DIR/spark-env.sh
    echo "export SPARK_LOCAL_DIRS=$SPARK_LOCAL_DIRS" >> $SPARK_CONF_DIR/spark-env.sh

    if [[ $SPARK_IPOIB == 1 ]]; then
        echo "" >> $SPARK_CONF_DIR/spark-env.sh
        echo "# Overwrite master IP" >> $SPARK_CONF_DIR/spark-env.sh
        echo "export SPARK_MASTER_IP=$SPARK_MASTER_IP" >> $SPARK_CONF_DIR/spark-env.sh
        echo "" >> $SPARK_CONF_DIR/spark-env.sh
        echo "# Overwrite local IP" >> $SPARK_CONF_DIR/spark-env.sh
        echo "export SPARK_LOCAL_IP=ib-\$(hostname)" >> $SPARK_CONF_DIR/spark-env.sh
    fi
}


function spark-start() {
    # setup spark environment
    spark-init $@

    # start master and slaves
    start-master.sh
    start-slaves.sh

    # spark URL
    export SPARK_URL="spark://$SPARK_MASTER_IP:7077"
    echo
    echo
    echo "Please use environment variable \$SPARK_URL, which is set to $SPARK_URL to connect to spark cluster."
}


function spark-stop() {
    # stop master and slaves
    stop-slaves.sh
    stop-master.sh
}

function spark-usage() {
    local PROMPT="[$USER@$HOSTNAME $PWD]\$"
    echo "# Start Spark On Demand"
    echo "$PROMPT spark-start"
    echo
    echo "# Example 1"
    echo "$PROMPT spark-submit --master \$SPARK_URL \$SPARK_DIR/examples/src/main/python/pi.py"
    echo
    echo "# Example 2"
    echo "$PROMPT spark-submit --master \$SPARK_URL \$SPARK_DIR/examples/src/main/python/wordcount.py input"
    echo
    echo "# Stop Spark On Demand"
    echo "$PROMPT spark-stop"
}
