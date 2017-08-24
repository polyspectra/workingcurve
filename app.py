import dash
import numpy as np
import pandas as pd
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_html_components as html
import plotly.graph_objs as go
import os

app = dash.Dash(__name__)
server = app.server
server.secret_key = os.environ.get('SECRET_KEY', 'my-secret-key')

app.layout = html.Div([
	html.Div(children='''
        A working curve helper written in Dash:
    '''),
    html.Div('Penetration Depth:'),
    dcc.Input(id='dp', value='500', type="number"),
    html.Div('Critical Exposure:'),
    dcc.Input(id='ec', value='40', type="number"),
    html.Div(id='my-div'),
    dcc.Graph(
	    style={'height': 300},
	    id='my-graph'
	)		
])

@app.callback(
    Output(component_id='my-graph', component_property='figure'),
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value')]
)
def update_graph(dp,ec):
	N = 500
	exp = np.linspace(0.5 * int(ec), 10 * int(ec), N)
	cd = int(dp)*np.log(exp / int(ec))
	# random_y = np.random.randn(N)


	traces = []
	traces.append(go.Scatter(x = exp,y = cd, mode='lines'))

	return {
	'data': traces,
	'layout': go.Layout(
		            title='Working Curve',
		            showlegend=False,
		            margin=go.Margin(l=50, r=50, t=40, b=20),
                    yaxis=dict(
                        range=[0,1500],
                        title= 'Cure Depth (µm)'
                    ),
                    xaxis=dict(
                        title= 'Exposure (mJ/cm2)'
                    )

		        )
	}	
    
if __name__ == '__main__':
    app.run_server()