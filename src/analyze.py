import os
import pandas as pd
import numpy as np
import re
from decimal import Decimal
from collections import defaultdict

from tool import fixturedata
from tool import namematch

import importlib
importlib.reload(fixturedata)

if __name__=='__main__':

    df = fixturedata.build_fixture_dataframe()
    

