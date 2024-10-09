#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from pathlib import Path
from dotenv import load_dotenv

import pandas as pd
import glob
import os

load_dotenv("../.env")


# In[ ]:


DATA_CSV = Path("../data/csv/")


# # Level 2: Processing CSV
# 
# **Note**  
# Low level dataframes processing (like converting datetimes, filtering, dropping duplicates, sorting) is done in the previous notebook. Here we assume that the data is already cleaned and ready for further processing.

# In[ ]:


csv_paths = glob.glob(os.path.join(DATA_CSV, "*.csv"))
for path in csv_paths:
    df = pd.read_csv(path)
    print(df)

