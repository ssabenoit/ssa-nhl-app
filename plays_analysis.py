"""
plays_analysis.py

performs various visualizations based on play by play data in our nhl database
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app import nhl_snowflake
from PIL import Image
import requests
import cairosvg
from io import BytesIO
pd.set_option("display.max_columns", None)

# custom color scale for rink heat maps
color_scale = [
    [0.0000, 'rgba(0, 0, 255, 0.0)'],  # Transparent blue
    [0.0417, 'rgba(0, 64, 255, 0.07)'],  # Light blue
    [0.0833, 'rgba(0, 128, 255, 0.14)'],  # Brighter blue
    [0.1250, 'rgba(0, 192, 192, 0.21)'], # Blue-green
    [0.1667, 'rgba(0, 255, 114, 0.28)'],  # Greenish blue
    [0.2083, 'rgba(0, 255, 50, 0.35)'],  # Light green
    [0.2500, 'rgba(0, 255, 0, 0.4)'],    # Bright green
    [0.2917, 'rgba(64, 255, 0, 0.42)'],  # Yellow-green
    [0.3333, 'rgba(128, 255, 0, 0.44)'],  # More yellow-green
    [0.3750, 'rgba(192, 255, 0, 0.47)'], # Yellow approaching
    [0.4167, 'rgba(255, 255, 0, 0.5)'],  # Yellow
    [0.4583, 'rgba(255, 224, 0, 0.50)'], # Yellow-orange
    [0.5000, 'rgba(255, 192, 0, 0.52)'], # More orange
    [0.5417, 'rgba(255, 160, 0, 0.56)'], # Orange
    [0.5833, 'rgba(255, 128, 0, 0.60)'], # Deep orange
    [0.6250, 'rgba(255, 96, 0, 0.63)'],   # Reddish orange
    [0.6667, 'rgba(255, 64, 0, 0.67)'],  # Orange-red
    [0.7083, 'rgba(255, 32, 0, 0.70)'],  # Approaching red
    [0.7500, 'rgba(255, 0, 0, 0.71)'],   # Bright red
    [0.7917, 'rgba(224, 0, 0, 0.73)'],   # Deep red
    [0.8333, 'rgba(192, 0, 0, 0.75)'],   # Darker red
    [0.8750, 'rgba(160, 0, 0, 0.77)'],    # Even darker red
    [0.9167, 'rgba(128, 0, 0, 0.78)'],    # Very deep red
    [0.9583, 'rgba(96, 0, 0, 0.79)'],     # Almost maroon
    [1.0000, 'rgba(64, 0, 0, 0.8)']      # Darkest red
]

def black_to_white(image_path):
    """Converts black background to white in an image."""

    with Image.open(image_path) as img:
        img = img.convert('RGBA')  # Convert to RGBA to handle transparency

        data = img.getdata()

        new_data = []
        for item in data:
            if item[0] == 0 and item[1] == 0 and item[2] == 0:  # Check if pixel is black
                new_data.append((255, 255, 255, item[3]))  # Replace black with white
            else:
                new_data.append(item)  # Keep other pixels unchanged

        img.putdata(new_data)
        return img
    

def visualize_rink():

    app = nhl_snowflake()
    faceoffs = app.get_plays() # play_type='faceoff'
    print(faceoffs)

    fig = px.scatter(faceoffs, x='X_POS', y='Y_POS', color='DESCRIPTION')
    rink = Image.open('rinks/rink_6.png')
    
    # img = requests.get("https://secure.espncdn.com/redesign/assets/img/nhl/bg-rink.svg")
    # print(img)
    # print(img.status_code)

    # img = cairosvg.svg2png(img.content)
    # img = BytesIO(img)
    # img = black_to_white(img)

    fig.add_layout_image(
        x=0,
        y=0,
        source=rink,
        xref="x",
        yref="y",
        sizex=200,
        sizey=85,
        sizing='stretch',
        xanchor="center",
        yanchor="middle",
        layer='below'
    )
    fig.update_xaxes(range=[-100, 100])
    fig.update_yaxes(range=[-42.5, 42.5])

    fig.show()
    # return fig

def visualize_single_game(game=2024020001):

    # get the plays for the given game
    app = nhl_snowflake()
    plays = app.get_plays(game=game) # play_type='faceoff'
    # print(plays.columns)
    # print(plays)

    # filter all types of shots and goals only
    desried_plays = ['shot-on-goal', 'blocked-shot', 'missed-shot', 'goal']
    plays = plays[plays['DESCRIPTION'].isin(desried_plays)]

    # adjust x and y positions based on offense zone side (for a half rink, with goal on the right)
    half_x, half_y = [], []
    for idx, row in plays.iterrows():
        if row['HOME_ABV'] == row['PLAY_TEAM_ABV'] and row['HOME_SIDE'] == 'right':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        elif row['AWAY_ABV'] == row['PLAY_TEAM_ABV'] and row['HOME_SIDE'] == 'left':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        else:
            half_x.append(row['X_POS'])
            half_y.append(row['Y_POS'])
    plays['x_half'] = half_x
    plays['y_half'] = half_y

    # generate the shot chart
    fig = px.scatter(plays, x='x_half', y='y_half', symbol='DESCRIPTION', color='PLAY_TEAM_ABV')
    rink = Image.open('rinks/rink_6.png')

    ### format the legend
    # only keep the colored circles for each team
    for i, trace in enumerate(fig.data):
        name = trace.name.split(',')
        if name[1] != ' shot-on-goal':
            trace['name'] = ''
            trace['showlegend']=False
        else:
            trace['name'] = name[0]
    
    # add in the symbols to the legend
    symbols = ['circle', 'square', 'diamond', 'x']
    for play, tick in zip(desried_plays, symbols):
        play = play.replace('-', ' ').title()

        fig.add_trace(go.Scatter(
            y=[None], mode='markers', marker=dict(size=5, symbol=tick, color='black'), name=play,
        ))

    # generate format the final rink
    fig.add_layout_image(
        x=0,
        y=0,
        source=rink,
        xref="x",
        yref="y",
        sizex=200,
        sizey=85,
        sizing='stretch',
        xanchor="center",
        yanchor="middle",
        layer='below'
    )
    fig.update_xaxes(range=[0, 100], showgrid=False, zeroline=False, showticklabels=False, title='')
    fig.update_yaxes(range=[-42.5, 42.5], showgrid=False, zeroline=False, showticklabels=False, title='')
    fig.update_layout(legend=dict(title='Shots Legend'))

    # fig.show()
    return fig

def full_rink_heatmap(team='NSH'):

    app = nhl_snowflake()
    data = app.get_plays(play_type='shot-on-goal', team=team)
    data = data[data['PLAY_TEAM_ABV'] == team]
    print(data)

    fig = px.density_heatmap(data, x='X_POS', y='Y_POS', nbinsx=100, nbinsy=60, color_continuous_scale=color_scale)

    rink = Image.open('rink_6.png')
    fig.add_layout_image(
        x=0,
        y=0,
        source=rink,
        xref="x",
        yref="y",
        sizex=200,
        sizey=85,
        sizing='stretch',
        xanchor="center",
        yanchor="middle",
        layer='below'
    )
    fig.update_xaxes(range=[-100, 100])
    fig.update_yaxes(range=[-42.5, 42.5])

    return fig

def half_rink_heatmap(team='NSH'):

    # retrieve all the plays of a certain type for the given team
    app = nhl_snowflake()
    shots = ('shot-on-goal', 'missed-shot')
    data = app.get_plays(play_type='shot-on-goal', team=team)
    
    if team != 'all':
        data = data[data['PLAY_TEAM_ABV'] == team]
    print(data.columns)
    print(len(data))

    # adjust x and y positions based on offense zone side
    half_x, half_y = [], []
    for idx, row in data.iterrows():
        if row['HOME_ABV'] == team and row['HOME_SIDE'] == 'right':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        elif row['AWAY_ABV'] == team and row['HOME_SIDE'] == 'left':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        else:
            half_x.append(row['X_POS'])
            half_y.append(row['Y_POS'])

    data['x_half'] = half_x
    data['y_half'] = half_y

    # generate the heat map
    fig = px.density_heatmap(data, x='x_half', y='y_half', nbinsx=100, nbinsy=60, color_continuous_scale=color_scale,
                             height=800, width=1000)

    # format the rink and figure size
    rink = Image.open('rink_6.png')
    fig.add_layout_image(
        x=0,
        y=0,
        source=rink,
        xref="x",
        yref="y",
        sizex=200,
        sizey=85,
        sizing='stretch',
        xanchor="center",
        yanchor="middle",
        layer='below'
    )
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(range=[-42.5, 42.5])

    # fig.show()
    return fig

def half_rink_heatmap_smooth(team='NSH'):

    # retrieve all the plays of a certain type for the given team
    app = nhl_snowflake()
    shots = ('shot-on-goal', 'missed-shot')
    data = app.get_plays(play_type='shot-on-goal', team=team)
    
    if team != 'all':
        data = data[data['PLAY_TEAM_ABV'] == team]
    print(data.columns)
    print(len(data))

    # adjust x and y positions based on offense zone side
    half_x, half_y = [], []
    for idx, row in data.iterrows():
        if row['HOME_ABV'] == team and row['HOME_SIDE'] == 'right':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        elif row['AWAY_ABV'] == team and row['HOME_SIDE'] == 'left':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        else:
            half_x.append(row['X_POS'])
            half_y.append(row['Y_POS'])

    data['x_half'] = half_x
    data['y_half'] = half_y

    # generate the heat map
    fig = go.Figure(
        data = go.Histogram2d(
            x = data['x_half'].to_list(),
            y = data['y_half'].to_list(),
            nbinsx=100, 
            nbinsy=60,
            colorscale = color_scale,
            zsmooth='best'
        )
    )

    # format the rink and figure size
    rink = Image.open('rinks/rink_6.png')
    fig.add_layout_image(
        x=0,
        y=0,
        source=rink,
        xref="x",
        yref="y",
        sizex=200,
        sizey=85,
        sizing='stretch',
        xanchor="center",
        yanchor="middle",
        layer='below'
    )
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(range=[-42.5, 42.5])
    fig.update_layout(
        height=900,
        width=1000,
    )

    fig.show()
    return fig

# visualize_single_game()
half_rink_heatmap_smooth()
