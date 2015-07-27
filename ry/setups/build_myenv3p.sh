rm -rf ~/miniconda/envs/myenv3p
conda create -y -n myenv3p  python=3 pip
source activate myenv3p 
conda install -y cython
conda install -y numpy

cd ~/src/mpi4py/
env  MPICC=/global/software/sl-6.x86_64/modules/intel/2013_sp1.4.211/openmpi/1.6.5-intel/bin/mpicc python setup.py install

export CC=/global/software/sl-6.x86_64/modules/intel/2013_sp1.4.211/openmpi/1.6.5-intel/bin/mpicc

cd ~/src/h5py
git checkout 2.5_add_include
python setup.py configure --hdf5=/global/software/sl-6.x86_64/modules/gcc/4.4.7/hdf5/1.8.11-gcc-p/ --mpi 
python setup.py build
python setup.py install

conda install -y ipython ipython-notebook ipython-qtconsole pandas matplotlib
conda install pytables

