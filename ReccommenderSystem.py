# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 01:17:36 2019
Modified on Sun March 03 13:20:22 2019
@author: adity
"""
import pandas as pd
from apyori import apriori, load_transactions
#importing the dataset
dataset=pd.read_excel('Invoice_Dataset_v2.xlsx')
doi=dataset[['InvoiceId','ErpProductid','ErpProductDesc']]
uniqinvoices=doi.InvoiceId.unique()
noofrows=len(doi.index)
transactions=[]
for i in uniqinvoices:
    mylist=[]
    for j in range(noofrows):
        if i==int(doi.iloc[j,0]):
            mylist.append(doi.iloc[j,2])
    if len(mylist)>0:
        transactions.append(mylist)

#Writing results to a excel so that we do not have to run the above it all again
listoflists = transactions
df = pd.DataFrame.from_dict({'Transactions in one invoice':listoflists})
df.to_excel('listoflists.xlsx', header=True, index=False)

#Traing data on Apriori Model
rules=apriori(transactions, min_support=0.0045, min_confidence=0.2)
#Visualising the results
results=list(rules)
for item in results:
    pair = item[0]
    items = [x for x in pair]
    print("Rule: " + items[0] + "," + items[1],",Supp: " + str(item[1]),",Conf: " + str(item[2][0][2]),",Lf: " + str(item[2][0][3]))