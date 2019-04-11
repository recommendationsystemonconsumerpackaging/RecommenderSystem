#  -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 01:17:36 2019
Modified on 12:30 PM 4/11/2019
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
import plotly.graph_objs as go


def masking_groupby(keys, values):
    keys = np.asarray(keys)
    values = np.asarray(values)
    return {key: values[keys == key].tolist()
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


def read_csv_last_run():
    df = pd.read_csv('apriori-output-n.csv')
    return df


def create_scatter_figure(df):
    figure = {
        'data': [
            go.Scatter(
                x=df['Lift'],
                y=df['Support'],
                mode='markers',
                marker={
                    "color": df['Confidence'],
                    "colorscale": [
                        [0, "#e8f5ab"], [0.09090909090909091, "#dcdb89"], [0.18181818181818182, "#d1c16b"],
                        [0.2727272727272727, "#c7a853"], [0.36363636363636365, "#ba8f42"],
                        [0.45454545454545453, "#aa793c"], [0.5454545454545454, "#97673a"],
                        [0.6363636363636364, "#815738"], [0.7272727272727273, "#684835"],
                        [0.8181818181818182, "#503b2e"], [0.9090909090909091, "#392d25"], [1, "#221e1b"]],
                    "colorsrc": "amitparmar01:0:618191",
                    "size": df['Support'],
                    "sizemode": "area",
                    "sizeref": 0.01956641975308642,
                    "sizesrc": "amitparmar01:0:0012e6",
                    "reversescale": False
                },
                text=df['Relations']
            )
        ],
        'layout': go.Layout(
            title='Product Association Scatter Plot',
            xaxis={
                "autorange": True,
                "title": {"text": "Lift"},
                "type": "linear"
            },
            yaxis={
                "autorange": True,
                "title": {"text": "Support %"},
                "type": "linear"
            }
        )
    }

    return figure


def run_dash_data_table():

    df = read_csv_last_run()
    support, confidence = get_last_run_paramters()

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'https://codepen.io/chriddyp/pen/brPBPO.css']
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
        html.Hr(),
        html.Div(id='intermediate-value', style={'display': 'none'}),
        html.Div(
            dcc.Graph(
                id='scatter-chart'
            )
        ),
        html.Hr(),
        html.Div([dash_table.DataTable(
            id='datatable-int',
            columns=[{'name': c, 'id': c} for c in df.columns if c != 'Relations'],
            data=df.to_dict("rows"),
            sorting=True,
            filtering=False,
            pagination_mode=False,
        )])
    ])

    @app.callback(Output('datatable-int', 'data'),
                  [Input('intermediate-value', 'children')])
    def update_output(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        return dff.to_dict("rows")

    @app.callback(Output('intermediate-value', 'children'),
                  [Input('submit-button', 'n_clicks')],
                  [State('input-1-support', 'value'),
                   State('input-2-confidence', 'value')])
    def get_new_data(n_clicks, support_val, confidence_val):

        if n_clicks != 0:
            if support_val != 'Support' and confidence_val != 'Confidence':
                dff = run_apriori(support=float(support_val), confidence=float(confidence_val))
            else:
                dff = read_csv_last_run()
        else:
            dff = read_csv_last_run()

        return dff.to_json(date_format='iso', orient='split')

    @app.callback(Output('scatter-chart', 'figure'),
                  [Input('intermediate-value', 'children')])
    def update_scatter_plot(jsonified_cleaned_data):
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        return create_scatter_figure(dff)

    @app.callback(Output('data-params', 'children'),
                  [Input('submit-button', 'n_clicks')],
                  [State('input-1-support', 'value'),
                   State('input-2-confidence', 'value')])
    def update_parameters(n_clicks, support_val, confidence_val):

        if n_clicks == 0:
            support_val, confidence_val = get_last_run_paramters()

        if support_val and confidence_val:
            return "Support: {0} |  Confidence: {1}".format(support_val, confidence_val)
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
    rules = apriori(transactions.values(), min_support=support, min_confidence=confidence)
    # rules = apriori(extract_colors(transactions), min_support=support, min_confidence=confidence)

    # Visualising the results
    results = list(rules)

    data_results = []
    for item in results:
        pair = item[0]
        items = [x for x in pair]
        if len(items) > 1:
            data_results.append(tuple([items[0], items[1], round(item[1]*100,4),
                                       round(item[2][0][2] * 100, 4), item[2][0][3],
                                       '{0} ---> {1} (C={2}%)'.format(items[0], items[1],
                                                                     round(item[2][0][2] * 100, 4))]))

    dff = pd.DataFrame.from_records(data_results, columns=['Antecedant', 'Descendant', 'Support', 'Confidence', 'Lift',
                                                           'Relations'])
    dff.to_csv('apriori-output-n.csv', encoding='utf-8', index=False)

    with open('last_run.txt', 'w') as f:
        f.write('{0}, {1}'.format(support, confidence))

    return dff


def main():

    print('starting')

    run_apriori()

    run_dash_data_table()


if __name__ == '__main__':
    main()
