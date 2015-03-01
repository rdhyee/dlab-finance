# dlab-finance
Machine learning on the TAQ data

#.bashrc setup
#-------------------------------------------------------------------------------
export MODULEPATH=$MODULEPATH:/global/software/sl-6.x86_64/modfiles/python/2.7.8
module load scikit-learn
# numpy and scipy are installed from above
module load matplotlib
module load pandas
# are these needed?
module load ipython
module load jinja2
module load pyzmq
module load tornado
# these would have issues
#module load prettyplotlib
#module load pyparsing

# data file
tradedata="/global/scratch/aculich/mirror/EQY_US_ALL_TRADE"
quotedata="/global/scratch/aculich/mirror/EQY_US_ALL_BBO"
#------------------------------------------------------------------------
