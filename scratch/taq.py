#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import sys
from random import random
from operator import add

from pyspark import SparkContext


if __name__ == "__main__":
    """
        Usage: pi [slices]
    """
    sc = SparkContext(appName="TAQProcessing")
    data = sc.textFile("/global/scratch/rsoni/testdata/taqtrade20100104")
    records = data.map(lambda s: [s[:9],s[9:10],s[10:26],s[26:30],s[30:39],s[39:50],s[50:51],s[51:53],s[53:69],s[69:70],s[70:71],s[71:73]])
    saperec = records.filter(lambda rec: rec[2]=='SAPE')
    print records.take(5)
    print records.count()
