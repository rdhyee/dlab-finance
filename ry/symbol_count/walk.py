import fnmatch
import os
import re
import datetime

from itertools import islice

BBO_BASE_DIR = "/global/scratch/aculich/mirror/EQY_US_ALL_BBO"
BBO_LABEL = "EQY_US_ALL_BBO"


def bbo_path_to_datetime(path):
    """
    takes a path to a file and returns the datetime.date of the file
    
    assumption that filename has form {label_date.zip}
    """

    g = re.search(r'(\d{4})(\d{2})(\d{2}).zip', path)
    if g:
        return datetime.datetime(*map(int,g.groups()))
    else:
        return None
    

def date_to_bbo_path(d):
    """
    takes input d (datetime.date) and returns a string with the full path to the corresponding BBO file
    """
    return "{base_dir}/{label}_{year:04d}/{label}_{year:04d}{month:02d}/{label}_{year:04d}{month:02d}{day:02d}.zip".format(
              base_dir=BBO_BASE_DIR,
              label=BBO_LABEL,
              year=d.year, month=d.month, day=d.day)
    
def standard_taq_files(root):
    
    for root, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if re.search(r'(\d{4})(\d{2})(\d{2}).zip', filename):
                yield (os.path.join(root, filename))
                

def taq_files_in_range(root, min_dt=None, max_dt=None):
    for root, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if re.search(r'(\d{4})(\d{2})(\d{2}).zip', filename):
                fpath = os.path.join(root, filename)
                dt = bbo_path_to_datetime(fpath)
                if not(((min_dt is not None) and dt < min_dt) or ((max_dt is not None) and dt > max_dt)):
                    yield fpath

def write_taskfile(fname="/global/scratch/ryee/symbol_count/taskfile", 
                   task="/global/home/users/ryee/dlab-finance/ry/symbol_count/count_symbols.py",
                   min_dt=None,
                   max_dt=None):

    with open(fname, "w") as tfile:
        for f in sorted(taq_files_in_range("/global/scratch/aculich/mirror/EQY_US_ALL_BBO", 
                                                min_dt=min_dt,
                                                max_dt=max_dt
                                            )):
            tfile.write("{0} {1}\n".format(task, f))


if __name__ == "__main__":
    write_taskfile(min_dt=datetime.datetime(2011,1,1), max_dt= datetime.datetime(2015,12,31))

