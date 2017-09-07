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
    dcc.Markdown('''
# Stereolithography Print Settings Utility:

#### Built with love by [polySpectra](http://polyspectra.com)
'''),
    dcc.Markdown('''
## Photopolymer Working Curve:
'''),
    html.Div('Penetration Depth (microns):'),
    dcc.Input(id='dp', value='120', type="number"),
    html.Div('Critical Exposure (mJ / cm^2):'),
    dcc.Input(id='ec', value='25', type="number"),
    html.Div(id='my-div'),
    dcc.Graph(
        style={'height': 300},
        id='my-graph'
    ),
    dcc.Markdown('''
## Solve the Exposure for a Specific Cure Depth:
'''),
    html.Div('Cure Depth (microns):'),
    dcc.Input(id='cd', value='1', type="number"),
    html.Div(id='expSolve', children='''Set exposure to: n/a'''),
dcc.Markdown('''
## Helpful Metrics for Specific Print Settings:
'''),
        html.Div('Exposure (mJ / cm^2):'),
    dcc.Input(id='exp', value='0', type="number"),  
        html.Div('Slice Thickness (microns):'),
    dcc.Input(id='dz', value='10', type="number"),
    html.Div('"Maximum" Volumetric / Multilayer Exposure:'),
    html.Div(id='vol', children=''',
        n/a
    '''),
    html.Div('"Maximum" Print Through Exposure & Additional Cure Depth:'),
    html.Div(id='thru_exp', children='''
        n/a
    '''),   
dcc.Markdown('''
## Explanation: 

This is a utility to facilitate stereolithographic 3D printing (SLA / DLP).

**Penetration Depth:** The 'effective' absorption length (Naperian (natural) log)

**Critical Exposure:** The minimum exposure to cure an infinitesimally small film

**Cure Depth:** The thickness of the cured layer at a given exposure

**Exposure:** The energy density of the light at the window / resin surface (power density * time)

**Slice Thickness:** The z step size of the printer, aka layer thickness

**"Maximum" Volumetric / Multilayer Exposure:** This is the total exposure a 'bottom' layer would receive after subsequently printing _many_ layers on top of it. This is an attempt to quantify the total amount of light received by the layer.

**"Maximum" Print Through Exposure & Additional Cure Depth:** This is the 'extra' exposure an empty layer would receive after subsequently printing _many_ layers on top of it. This is an attempt to quantify the worse case scenario for "print through", the effect that printed layers are often thicker than the desired layer thickness / cure depth, because light from subsequent layers bleeds through. Both the extra "print-through" exposure and corresponding "print-through" cure depth are calculated. The bigger this number, the larger the error on the dimensional accuracy of 'overhung' features.



## Assumptions: 

This utility only accounts for Beer's Law absorption, which means that there is no scattering accounted for in the optics. It also assumes that the Ec and Dp of the photopolymer do not change throughout the print process. The "maximum" print through assumes that 1000 layers 'on top' is enough to account for the excess light from subsequently printed layers. It also assumes that there is still liquid resin around to be polymerized (ie - the resin bath level is very high). 

## References:

* P.F. Jacobs - Fundamentals of Stereolithography


'''),

])  


#this callback updates the working curve graph
@app.callback(Output(component_id='my-graph', component_property='figure'),    
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value')
    ]) 



def update_wc(dp,ec):

    traces = working_curve(dp,ec)

    return {
    'data': traces,
    'layout': go.Layout(
                    title='Working Curve',
                    xaxis=dict(                 # all "layout's" "xaxis" attributes: /python/reference/#layout-xaxis
                        title="mJ / cm^2"            # more about "layout's" "xaxis's" "title": /python/reference/#layout-xaxis-title
                    ),
                    yaxis=dict(                 # all "layout's" "xaxis" attributes: /python/reference/#layout-xaxis
                        title="microns"            # more about "layout's" "xaxis's" "title": /python/reference/#layout-xaxis-title
                    ),
                    showlegend=False,
                    margin=go.Margin(l=50, r=50, t=40, b=40),
                    annotations=[
                             # dict(                            # all "annotation" attributes: /python/reference/#layout-annotations
                    #           text="simple annotation",
                    #           )
                             ]
                )
    }   


def working_curve(dp,ec): 
    #number of data points
    N = 1000    
    #exposure array from 0.5ec to 10ec                                      
    expo = np.linspace(0.5 * float(ec), 10 * float(ec), N)
    #calculate the cure depth
    cd = float(dp)*np.log(expo / float(ec))

    #build the xy matrix for plotting
    traces = []
    traces.append(go.Scatter(x = expo,y = cd, mode='lines'))

    return traces


#this callback updates the exposure
@app.callback(Output(component_id='expSolve', component_property='children'),    
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value'),
    Input(component_id='cd', component_property='value')
    ]) 
        

def exposure(dp,ec,cd):
    if(float(cd) > 0 and float(dp)>0):
        exp = np.exp(float(cd) / float(dp)) * float(ec)

        return '''Set exposure to: ''' + str(exp)

    else:
        return '''Set exposure to: n/a'''


#this callback updates the cure depth
@app.callback(Output(component_id='cd', component_property='value'),    
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value'),
    Input(component_id='exp', component_property='value')
    ]) 



def cd_update(dp,ec,exp):
    if(float(exp)>0 and float(ec)>0):
        cd = cure_depth(dp,ec,exp)

        if(cd > 0):
            return str(cd)
        else:
            return None
    else:
        return None

def cure_depth(_dp,_ec,_exp):
    _cd = float(_dp)*np.log(float(_exp) / float(_ec))

    return _cd




#this callback updates the volumetric exposure
@app.callback(Output(component_id='vol', component_property='children'),    
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value'),
    Input(component_id='exp', component_property='value'),
    Input(component_id='dz', component_property='value'),
    ]) 

def volumetric_exp(dp,ec,exp,dz):

    limit = 1000

    add = 0
    for i in range(0,limit):
        add = add + (float(exp) * np.exp(-(float(dz)*i) / float(dp)))

    return str(add) + ''' mJ / cm^2 volumetric exposure'''


#this callback updates the print through exposure
@app.callback(Output(component_id='thru_exp', component_property='children'),    
    [Input(component_id='dp', component_property='value'),
    Input(component_id='ec', component_property='value'),
    Input(component_id='exp', component_property='value'),
    Input(component_id='dz', component_property='value'),
    ]) 

def thru_exp(dp,ec,exp,dz):

    limit = 1000

    add = 0
    for i in range(1,limit):
        add = add + (float(exp) * np.exp(-(float(dz)*i) / float(dp)))

    
    
    thru = cure_depth(dp,ec,add)
    if(thru < 0.00):
        thru = 0

    return str(add) + ''' mJ / cm^2 "print through" exposure and 

    ''' + str(thru) + ''' microns "print through" cure depth '''

	
    
if __name__ == '__main__':
    app.run_server()