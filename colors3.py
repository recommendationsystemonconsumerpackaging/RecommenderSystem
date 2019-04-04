#!/usr/bin/env python
# coding: utf-8

# In[1]:


from os import path
import numpy as np
import pandas as pd
import csv
import webcolors as wc


# In[2]:


fname = path.expanduser(r'C:\Users\Shashank\Documents\MODPAC\d2.csv')


# In[3]:


dfr = pd.read_csv(fname)
dfr1 = dfr.sort_values(by ='ErpProductDesc' ,ascending = True)
a = dfr1.ErpProductDesc.unique()
d = {}


# In[4]:


def check_for_color(s):
    c = wc.CSS3_NAMES_TO_HEX.keys()
    l = s.lower().split()
    for word in l:
        if word in c:
            return word
            break
    return None

for item in a:
    match = check_for_color(item)
    if match is not None:
        d[item] = match
    else:
        d[item] = 'no colour'
        



# In[6]:


def get_product_color(pdesc):
    return d[pdesc]

dfr1['ProductColor'] = dfr1['ErpProductDesc'].apply(get_product_color)
    


# In[7]:


dfr1.head()


# In[8]:


dfr1.tail()


# In[10]:


dfr2 = dfr1.groupby('ProductColor')['LineTotalAmount'].sum()


# In[11]:


dfr2.head()


# In[12]:


dfr2


# In[16]:


dfr1.to_csv('WithColourData.csv')


# In[17]:


dfr2.to_csv('ColorAmount.csv',header = False)


# In[ ]:




