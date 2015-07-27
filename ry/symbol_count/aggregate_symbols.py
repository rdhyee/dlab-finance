#!/global/home/users/ryee/miniconda/envs/myenv3/bin/python

import glob
from itertools import islice

import tables as tb

from count_symbols import  (SymbolCount, bbo_path_to_datetime)

if __name__ == '__main__':

	with tb.open_file("/global/scratch/ryee/symbol_count/agg_count.h5", mode="w") as aggfile:
		root = aggfile.root
		c_table = aggfile.createTable(root, "count_table", SymbolCount )	
       	
		for (i,f) in enumerate(islice(glob.glob("/global/scratch/ryee/symbol_count/output/*.h5"),None)):
			print (i, f)
			with tb.open_file(f, mode="r") as dayfile:
				day_table = dayfile.root.count_table.read()
				c_table.append(day_table)
				c_table.flush()