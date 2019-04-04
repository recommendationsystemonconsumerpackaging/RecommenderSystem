#  -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 01:17:36 2019
Modified on 12:30 PM 3/27/2019
@authors: adity
          Amit Parmar (amitparm@buffalo.edu)
"""
import pandas as pd
from apyori import apriori
import pickle
import numpy as np
from colour import Color

import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State


def masking_groupby(keys, vals):
    keys = np.asarray(keys)
    vals = np.asarray(vals)
    return {key: vals[keys == key].tolist()
            for key in np.unique(keys)}


def deserialize_transactions():
    try:
        with open('transactions.pickle', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


def load_data_from_excel():
    dataset = pd.read_excel('Invoice_Dataset_v2.xlsx')

    transactions = masking_groupby(dataset[['BillingAddressErpId']], dataset[['ErpProductDesc']])

    with open('transactions.pickle', 'wb') as serialize:
        pickle.dump(transactions, serialize, pickle.HIGHEST_PROTOCOL)

    return transactions


def get_last_run_paramters():
    support, confidence = None, None
    try:
        with open('last_run.txt', 'r') as f:
            line = f.readline()
            support = float(line.split(',')[0])
            confidence = float(line.split(',')[1])
    except FileNotFoundError:
        support = 0.02
        confidence = 0.25

    return support, confidence


def run_dash_data_table():
    df = pd.read_csv('apriori-output-n.csv')

    support, confidence = get_last_run_paramters()

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

    app.layout = html.Div([
        html.H1(id='data-params', children="Support: {0} |  Confidence: {1}".format(support, confidence)),
        html.Hr(),
        html.Div([
            dcc.Input(id='input-1-support', type='text', value='Support'),
            dcc.Input(id='input-2-confidence', type='text', value='Confidence'),
            html.Button(id='submit-button', n_clicks=0, children='Submit'),
            html.Div(id='output-state')
        ]),
        html.Div(id='datatable-mod'),
        html.Hr(),
        html.Div([dash_table.DataTable(
            id='datatable-int',
            columns=[{'name': c, 'id': c} for c in df.columns],
            data=df.to_dict("rows"),
            sorting=True,
            filtering=True,
            pagination_mode=False,
        )])
    ])

    @app.callback(Output('datatable-int', 'data'),
                  [Input('submit-button', 'n_clicks')],
                  [State('input-1-support', 'value'),
                   State('input-2-confidence', 'value')])
    def update_output(n_clicks, support, confidence):

        if support != 'Support' and confidence != 'Confidence':
            dff = run_apriori(support=float(support), confidence=float(confidence))
            return dff.to_dict("rows")

    @app.callback(Output('data-params', 'children'),
                  [Input('submit-button', 'n_clicks')],
                  [State('input-1-support', 'value'),
                   State('input-2-confidence', 'value')])
    def update_parameters(n_clicks, support, confidence):

        if n_clicks == 0:
            support, confidence = get_last_run_paramters()

        if support and confidence:
            return "Support: {0} |  Confidence: {1}".format(support, confidence)
        else:
            return "Support: NA |  Confidence: NA"

    app.run_server(debug=True, port=8051)


def check_color(colorText):
    try:
        Color(colorText.replace('#', ''))
        return True
    except ValueError:
        return False


def extract_colors(transactions):
    colorsInfo = []

    for trans in transactions.values():
        itemsset = []
        for item in trans:
            info = [i for i in item.split(' ') if check_color(i)]
            if info:
                itemsset.append(info[0])
        if itemsset:
            colorsInfo.append(set(itemsset))

    return colorsInfo


def run_apriori(support=None, confidence=None):

    transactions = deserialize_transactions()

    if not transactions:
        transactions = load_data_from_excel()

    if not support and not confidence:
        support, confidence = get_last_run_paramters()

    # Training data on Apriori Model
    # rules = apriori(transactions.values(), min_support=support, min_confidence=confidence)
    rules = apriori(extract_colors(transactions), min_support=support, min_confidence=confidence)

    # Visualising the results
    results = list(rules)

    data_results = []
    for item in results:
        pair = item[0]
        items = [x for x in pair]
        if len(items) > 1:
            data_results.append(tuple([items[0], items[1], round(item[1]*100,4),
                                       round(item[2][0][2] * 100, 4), item[2][0][3]]))

    dff = pd.DataFrame.from_records(data_results, columns=['Antecedant', 'Descendant', 'Support', 'Confidence', 'Lift'])
    dff.to_csv('apriori-output-n.csv', encoding='utf-8', index=False)

    with open('last_run.txt', 'w') as f:
        f.write('{0}, {1}'.format(support, confidence))

    return dff


def main():
    # importing the dataset
    print('starting')

    run_apriori()

    run_dash_data_table()


if __name__ == '__main__':
    main()
