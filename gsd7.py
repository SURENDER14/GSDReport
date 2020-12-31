import pandas as pd
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output,State
import dash_table.DataTable
import json
import base64
import numpy as np
import io
import urllib
from dash.exceptions import PreventUpdate
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#Method for Region column from Country
def get_continent(Country):
    country =Country.lower()
    apac_list=['china','india','indonesia','pakistan','bangladesh','japan','philippines','vietnam','thailand',
    'myanmar','south korea','malaysia','nepal','north korea','australia','taiwan','sri lanka','cambodia',
    'papua new guinea','laos','singapore','new zealand','mongolia','timor-leste','fiji','bhutan','solomon islands',
    'maldives','brunei','vanuatu','new caledonia','french polynesia','samoa','guam','kiribati','micronesia','tonga',
    'marshall islands','northern mariana islands','american samoa','palau','cook islands','tuvalu','wallis and futuna',
    'nauru','niue','tokelau','united arab emirates']

    ce_list =['austria','belgium','bulgaria','croatia','czech republic','cyprus','denmark','estonia','finland','france',
    'germany','greece','hungary','iceland','italy','latvia','lithuania','liechtenstein','luxembourg','malta',
    'norway','netherlands','poland','portugal','romania','slovakia','slovenia','spain','sweden','switzerland','turkey']

    uk_list =['united kingdom', 'ireland']

    rest_of_na =['argentina','bolivia','brazil','chile','colombia','ecuador','guyana','paraguay','peru','suriname','uruguay', 'canada', 'mexico', 'el salvador', 'guatemala', 'honduras','venezuela']

    if country == 'united states':
        return 'NA'
    elif country in ce_list:
        return 'CE'
    elif country in uk_list:
        return 'UK'
    elif country in apac_list:
        return 'APAC'
    elif country in rest_of_na:
        return 'R NA'



app = dash.Dash(__name__,external_stylesheets=external_stylesheets)
app.layout = html.Div([
    
    dcc.Upload(id='upload-data',children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]), style={
        'width': '100%',
        'height': '60px',
        'lineHeight': '60px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center'
    }),
    html.Div(id='table-store',style={'display': 'none'}),
   
    html.Div([
    html.Div([
    dcc.Graph(id='donut-pending')
    ],style={'width': '29%','display': 'inline-block','border': 'thin lightgrey solid'}),
    html.Div([
    dcc.Graph(id='bar1')
    ],style={'width': '70%','display': 'inline-block','float': 'right','border': 'thin lightgrey solid'})
    ]),
      html.Div([
    html.Div([
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Analyst', 'value': 'Analyst'},
            {'label': 'Region', 'value': 'Region'},
            {'label': 'Status Reason', 'value': 'Status Reason'},
            {'label': 'Age', 'value': 'Age'},
            {'label': 'Priority', 'value': 'Priority'},
            {'label': 'Category', 'value': 'Category'}
        ],
        value='Region')
    ],style={'width': '48%','display': 'inline-block'}),
    html.Div([dcc.Dropdown(id='dropdown2',multi=True)
    ],style={'width': '48%','float': 'right',  'display': 'inline-block'})
    ]),
    html.Div([
    html.Div([
    dcc.Dropdown(id='dropdown3')
    ],style={'width': '48%','display': 'inline-block'}),
    html.Div([dcc.Dropdown(id='dropdown4',multi=True)
    ],style={'width': '48%','float': 'right',  'display': 'inline-block'})
    ]),
    dcc.Graph(id='bar'),
    dash_table.DataTable(id='table',style_cell={'textAlign': 'left'},export_format='csv')
])
#Store uploaded CSV to a hidden div
@app.callback(Output('table-store','children'),[Input('upload-data','contents')],[State('upload-data', 'filename')])
def upload_to_hidden_div(contents,filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
                            
            total_tickets = pd.read_csv(io.StringIO(decoded.decode('latin')),parse_dates=['Reported Date'],usecols=['Assigned to Individual', 'Incident Number', 'Reported Date', 'Region', 'Priority','Status_Reason','Requester Login Name','Category','Type','Item','Summary*'],
    dtype={'Assigned to Individual':'category','Region':'category','Priority':'category'})

        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            total_tickets = pd.read_excel(io.BytesIO(decoded))

    except Exception as e:
        return 'There was an error processing this file.'
    total_tickets['Status_Reason'].fillna(value='In Progress',inplace=True)
    total_tickets['Status_Reason']=total_tickets['Status_Reason'].astype('category')
    total_tickets['Age'] =(datetime.datetime.now()-total_tickets['Reported Date']).apply(lambda x:str(x.days)+" Day's")
    total_tickets.rename(columns={"Requester Login Name": "User ID", "Summary*": "Summary","Assigned to Individual":"Analyst","Status_Reason":"Status Reason","Region":"Country"},inplace=True)
    total_tickets['Region'] =total_tickets['Country'].apply(get_continent)
    total_tickets['Item']=total_tickets['Item'].apply(lambda x:' & '+x)
    total_tickets['Type & Item']=total_tickets['Type']+total_tickets['Item']
    total_tickets.drop(labels=['Type','Item'],axis='columns',inplace=True)
    return total_tickets.to_json(date_format='iso',orient='split')

#Generate Dropdown2,doughnut and bar figure
@app.callback([Output('dropdown2','options'),Output('donut-pending','figure'),Output('bar','figure')],[Input('dropdown','value'),Input('table-store','children')])
def fil_drop_down2(dropdown,table):
    total_tickets=pd.read_json(table,orient='split')
    
    options=[{'label': i, 'value': i} for i in total_tickets[dropdown].unique()]
    fig_pie = {'data':[go.Pie(
        labels =total_tickets['Region'].value_counts().index,
        values =total_tickets['Region'].value_counts().values,
        hole =0.3
      )],

    'layout' : go.Layout(
    title ="Overall Pending",
    annotations=[dict(text=len(total_tickets), x=0.5, y=0.5, font_size=20, showarrow=False)]
    )}
    fig_bar = {'data':[go.Bar(
        x =total_tickets[dropdown].value_counts(ascending=True).values,
        y =total_tickets[dropdown].value_counts(ascending=True).index,
        orientation='h')],

      'layout' : go.Layout(
    title ="Pending by {}".format(dropdown),
    xaxis=dict(automargin=True),
    yaxis=dict(automargin=True),
    margin = dict(t=30, b= 20, r=10)
     )
     }
    return options,fig_pie,fig_bar

# Day wise pending bar figure
@app.callback(Output('bar1','figure'),[Input('table-store','children')])
def bar1(table_store):
    total_tickets=pd.read_json(table_store,orient='split')
    total_tickets['Age']=total_tickets['Age'].apply(lambda x:int(x.split()[0]))
    def age_interval(Age):
        if Age == 0:
            return 'Same Day'
        elif Age==1:
            return '1 Day'
        elif Age==2:
            return '2 Day'
        elif Age==3:
            return '3 Day'
        elif Age==4 or Age==5:
            return '4 - 5 Day'
        elif Age>5 and Age<11:
            return '6 - 10 Day'
        elif Age>10 and Age<16:
            return '11 - 15 Day'
        elif Age>15 and Age<31:
            return '16 - 30 Day'
        else:
            return str(Age)
    total_tickets['Age Interval']=total_tickets['Age'].apply(age_interval)
    
    fig_bar = {'data':[go.Bar(
        x =total_tickets[total_tickets['Age Interval']==age]['Region'].value_counts(ascending=True).values,
        y =total_tickets[total_tickets['Age Interval']==age]['Region'].value_counts(ascending=True).index,
        orientation='h',name= age)for age in total_tickets['Age Interval'].unique()],

      'layout' : go.Layout(
    title ="Pending by Region and Age",
    barmode='stack',
    xaxis=dict(automargin=True),
    yaxis=dict(automargin=True),
    margin = dict(t=30, b= 20, r=10)
     )
     }
    return fig_bar
# Generate dropdown 3 options from dropdown1
@app.callback(Output('dropdown3','options'),
[Input('dropdown','value')])
def fill_dropdown3(dropdown):
    options=[
            {'label': 'By Analyst', 'value': 'Analyst'},
            {'label': 'By Region', 'value': 'Region'},
            {'label': 'By Status Reason', 'value': 'Status Reason'},
            {'label': 'By Age', 'value': 'Age'},
            {'label': 'By Priority', 'value': 'Priority'},
            {'label': 'Category', 'value': 'Category'},
            {'label': 'Type & Item', 'value': 'Type & Item'}
        ]      
    def get_option_from_value(value):
        if value=='Analyst':
            return {'label': 'By Analyst', 'value': 'Analyst'}
        if value=='Region':
            return  {'label': 'By Region', 'value': 'Region'}
        if value=='Status Reason':
            return  {'label': 'By Status Reason', 'value': 'Status Reason'}
        if value=='Age':
            return  {'label': 'By Age', 'value': 'Age'}
        if value=='Priority':
            return {'label': 'By Priority', 'value': 'Priority'}
        if value=='Category':
            return {'label': 'Category', 'value': 'Category'}
    options.remove(get_option_from_value(dropdown))
    return options
# Generate dropdown4 options from dropdown3 values
@app.callback(Output('dropdown4','options'),
[Input('dropdown3','value'),Input('table-store','children')],[State('dropdown','value'),State('dropdown2','value')])
def fill_dropdown4(dropdown3,table_store,dropdown,dropdown2):
    if dropdown3 is None:
        PreventUpdate
    total_tickets=pd.read_json(table_store,orient='split')
    filtered = total_tickets[total_tickets[dropdown].isin(dropdown2)]
    options=[{'label': i, 'value': i} for i in filtered[dropdown3].unique()]
    return options
# Geneate table based on dropdown values
@app.callback([Output('table','columns'),Output('table','data')],[Input('dropdown4','value'),Input('dropdown2','value'),Input('dropdown3','value'),Input('dropdown','value')],
[State('table-store','children')])
def filter(dropdown4,dropdown2,dropdown3,dropdown,table_store):
    if dropdown2 is None:
        PreventUpdate
    total_tickets=pd.read_json(table_store,orient='split')
    filtered = total_tickets[total_tickets[dropdown].isin(dropdown2)]
    if dropdown3 is None:
        filtered_2column=filtered.drop(labels=['Reported Date','Region','User ID'],axis='columns')
        filtered_2column['N'] = np.arange(1,len(filtered_2column)+1)
        filtered_2column=filtered_2column[['N','Analyst','Incident Number','Priority','Age','Category','Type & Item','Summary','Status Reason','Country']]
        columns=[{"name": i, "id": i} for i in filtered_2column.columns]
        data=filtered_2column.to_dict('records')
        return columns,data
        
    filtered2=filtered[filtered[dropdown3].isin(dropdown4)]
    filtered_2column=filtered2.drop(labels=['Reported Date','Region','User ID'],axis='columns')
    filtered_2column['N'] = np.arange(1,len(filtered_2column)+1)
    filtered_2column=filtered_2column[['N','Analyst','Incident Number','Priority','Age','Category','Type & Item','Summary','Status Reason','Country']]
    columns=[{"name": i, "id": i} for i in filtered_2column.columns]
    data=filtered_2column.to_dict('records')
    
    return columns,data


if __name__ == '__main__':
    app.run_server(debug=True)
