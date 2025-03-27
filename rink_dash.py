"""
rink_dash.py
Benoit Cambournac

renders simple dashboard for game rink charts and heat map
"""
import panel as pn
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from app import nhl_snowflake
from PIL import Image
import datetime as dt
from panel.theme import Bootstrap, Material, Native
# from io import BytesIO
# import requests
# import cairosvg
# from plays_analysis import visualize_rink

################ Dashboard Functions #############
# visualize the shot map for the given conditions
### not in use
def visualize_rink(game):

    app = nhl_snowflake()
    faceoffs = app.get_plays(game=game) # play_type='faceoff'
    # print(faceoffs)

    fig = px.scatter(faceoffs, x='X_POS', y='Y_POS', color='DESCRIPTION')
    rink = Image.open('rinks/rink_v_idk.jpeg')

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
    fig.update_xaxes(range=[-100, 100], showgrid=False, zeroline=False)
    fig.update_yaxes(range=[-42.5, 42.5], showgrid=False, zeroline=False)

    # fig.show()
    return fig

# visualize the shot map for a game on a single half
def visualize_single_game(game):

    # display an empty rink for an invalid game id
    
    # get the plays for the given game if it is a valid game
    # print(game)
    app = nhl_snowflake()
    plays = app.get_plays(game=game) # play_type='faceoff'

    if game is None or len(plays) == 0:
        fig = go.Figure()
        rink = Image.open('rinks/rink_12.png')
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
        fig.update_xaxes(
            range=[-100, 100], showgrid=False, zeroline=False, title='',
            tickmode='array', tickvals=[-50, 50], ticktext=['AWAY', 'HOME']
        )
        fig.update_yaxes(range=[-42.5, 42.5], showgrid=False, zeroline=False, showticklabels=False, title='')
        fig.update_layout(legend=dict(title='Shots Legend'), width=1300) 

        # print('skipped')
        return fig


    # determine the home side (for rink labeling)
    # if plays[plays['PERIOD'] == 1]['HOME_SIDE'].iloc[0] == 'right': side_labels = 
    # else: side_labels = ['HOME', 'AWAY']

    # filter all types of shots and goals only
    desried_plays = ['shot-on-goal', 'blocked-shot', 'missed-shot', 'goal']
    plays = plays[plays['DESCRIPTION'].isin(desried_plays)]
    

    # adjust x and y positions based on offense zone side (for a half rink, with goal on the right)
    half_x, half_y = [], []
    for idx, row in plays.iterrows():
        if row['HOME_ABV'] == row['PLAY_TEAM_ABV'] and row['HOME_SIDE'] == 'right':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        elif row['AWAY_ABV'] == row['PLAY_TEAM_ABV'] and row['HOME_SIDE'] == 'right':
            half_x.append(-1 * row['X_POS'])
            half_y.append(-1 * row['Y_POS'])
        else:
            half_x.append(row['X_POS'])
            half_y.append(row['Y_POS'])
    plays['x_half'] = half_x
    plays['y_half'] = half_y

    
    # pull in each teams color
    colors = pd.read_csv('teams.csv')
    plays = plays.merge(colors, left_on='PLAY_TEAM_ABV', right_on='TEAM_ABV', how='left')
    # goals = plays[plays['DESCRIPTION'] == 'goal']

    # print(plays.head())
    home_abv = plays.loc[0, 'HOME_ABV']
    away_abv = plays.loc[0, 'AWAY_ABV']
    # print(plays.iloc[-1,:])

    # compute goal totals
    goals = plays[plays['DESCRIPTION'] == 'goal'].groupby(by=['PLAY_TEAM_ABV'])['ID'].count()
    if home_abv not in goals.index:
        home_goals = 0
    else: home_goals = goals.loc[home_abv]

    if away_abv not in goals.index:
        away_goals = 0
    else: away_goals = goals.loc[away_abv]

    # update the summary line
    home_logo.object = Image.open(f'logos/{home_abv}.webp')
    away_logo.object = Image.open(f'logos/{away_abv}.webp')
    home_team.object = f"## {home_abv}"
    home_score.object = f"## {home_goals}"
    away_team.object = f"## {away_abv}"
    away_score.object = f"## {away_goals}"

    # create the visual
    fig = go.Figure()

    # add the team traces for the legend
    for team, col in set(zip(plays['PLAY_TEAM_ABV'], plays['color_hex'])):
        print(team, col)

        fig.add_trace(go.Scatter(
            y=[None], mode='markers', marker=dict(size=6, symbol='circle', color=col), name=team
        ))

    # add each shot trace to the scatter plot
    symbols = ['circle', 'square', 'diamond', 'x']
    for play, tick in zip(desried_plays, symbols):
        
        # extract the data for the current trace and format its title
        subset = plays[plays['DESCRIPTION'] == play]
        play = play.replace('-', ' ').title()
        
        # format tick size to highlight goals
        if play == 'Goal': tick_size=12;  alpha=0.9
        else: tick_size=7; alpha = 0.7

        # add the data trace
        fig.add_trace(go.Scatter(
        x=subset['x_half'], y=subset['y_half'], marker=dict(size=tick_size, symbol=tick, color=subset['color_hex']),
            mode='markers', showlegend=False, opacity=alpha
        ))

        # add the colorless trace for the legend
        fig.add_trace(go.Scatter(
            y=[None], mode='markers', marker=dict(size=tick_size, symbol=tick, color='black'), name=play, opacity=alpha
        ))
    

    ### format the legend
    # only keep the colored circles for each team
    # for i, trace in enumerate(fig.data):
    #     print(trace)
    #     name = trace.name.split(',')
    #     if name[1] != ' shot-on-goal':
    #         trace['name'] = ''
    #         trace['showlegend']=False
    #     else:
    #         trace['name'] = name[0]
    

    # generate format the final rink
    rink = Image.open('rinks/rink_12.png')
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
    fig.update_xaxes(
        range=[-100, 100], showgrid=False, zeroline=False, title='',
        tickmode='array', tickvals=[-50, 50], ticktext=['AWAY', 'HOME']
    )
    fig.update_yaxes(range=[-42.5, 42.5], showgrid=False, zeroline=False, showticklabels=False, title='')
    fig.update_layout(legend=dict(title='Shots Legend'), height=650)

    # fig.show()
    return fig

# gets and organizes the boxscore for the given game
def generate_boxscore(game, side='both'):

    # get the boxscore for the game
    app = nhl_snowflake()
    full_boxscore = app.get_game_box_score(game)
    # print(full_boxscore)

    ## TO add: updates Markdown or whatever to give a high level game summary

    # trim and format the table
    full_boxscore = full_boxscore[['NAME', 'TEAM_ABV', 'GOALS', 'ASSISTS', 'SHOTS', 'BLOCKS']]
    cols = [header.replace('_', ' ').title() for header in full_boxscore.columns]
    cols[1] = 'Team'
    full_boxscore.columns = cols

    
    full_boxscore = full_boxscore[(full_boxscore['Shots'] > 0)].drop_duplicates() # | (full_boxscore['Blocks'] > 0)
    full_boxscore.style.set_properties(**{'text-align': 'center'})

    return full_boxscore

# updates the options for the games filter based on the selected date
def update_games(event):

    # connect to the database and retrieve the games for the given day
    app = nhl_snowflake()
    print(date_picker.value)

    available_games, game_strings = app.get_games(date_picker.value)
    print(available_games)

    # format the options dictionary: {string id: int game_id}
    options = {game_string: game_id for game_string, game_id in zip(game_strings, available_games)}
    # print(options)

    game_selector.options = options
    if len(list(options.keys())) > 0:
        game_selector.value = options[list(options.keys())[0]]
    else:
        game_selector.value = None

# limits the date picker to only enabled days with games played
def set_available_games():

    app = nhl_snowflake()
    valid_dates = app.get_game_dates()
    
    date_picker.enabled_dates = valid_dates[1:]
    date_picker.value = dt.date(int(valid_dates[1][:4]), int(valid_dates[1][5:7]), int(valid_dates[1][8:]))
    update_games(None)

def table_click_callback(event):

    print(f'Clicked cell in {event.column!r} column, row {event.row!r} with value {event.value!r}')
    print(boxscore_pane.selected_dataframe)

# set panel extensions
pn.extension('plotly')
pn.extension('tabulator')
# pn.extension(sizing_mode='stretch_width')

custom_css = """

    .df-container {
        min-height: 400px;
    }

    @media (max-width: 767px) {
        
        .df-container {
            min-height: 400px;
        }
        
    }

    @media (min-width: 768px) {
        
        .df-container {
            min-height: 700px;
        }
        
    }
"""

########### create widgets and panes ##############
# dashboard row for filter widgets
date_picker = pn.widgets.DatePicker(name='Date Picker', value=dt.datetime.now() - dt.timedelta(days=1), design=Native)
game_selector = pn.widgets.Select(name='Select Game', value=None, options=[2024020001, 2024020002, 2024020003], design=Native)
# season_selector = pn.widgets.Select(name='Select Season', value='2024-2025', options=['2024-2025', '2023-2024'])
# team_selector = pn.widgets.Select(name='Select Team', value='NSH', options=['NSH', 'BOS', 'CHI', 'NYI']) 


# widgets for game summary row
home_logo = pn.pane.Image(Image.open('logos/BOS.webp'), height=50, width=50)
away_logo = pn.pane.Image(Image.open('logos/NSH.webp'), height=50, width=50)
at_symbol = pn.pane.Markdown("## @")
home_team = pn.pane.Markdown("## BOS", margin=(10, 0, 10, 10))
home_score = pn.pane.Markdown("## 5")
away_team = pn.pane.Markdown("## NSH", margin=(10, 0, 10, 0))
away_score = pn.pane.Markdown("## 6")
summary_row = pn.Row(away_team, away_logo, away_score, at_symbol, home_score, home_logo, home_team, margin=(10, 0)) 

filters_row = pn.FlexBox(pn.Spacer(width=50), date_picker, game_selector, summary_row, flex_wrap='nowrap', gap='50px')

set_available_games()

# widget callbacks
date_picker.param.watch(update_games, 'value')

# main plot widget for rink shot chart/ heat map
main_plot = pn.bind(
    visualize_single_game, 
    game=game_selector
)
plot_pane = pn.pane.Plotly(main_plot, sizing_mode="stretch_width") # , css_classes=['df-container'])


# dataframe widgets for the boxscore
boxscore = pn.bind(generate_boxscore, game=game_selector)
boxscore_pane = pn.pane.DataFrame(boxscore, index=False, max_rows=None, justify="center", max_width=1000,
                                  col_space=200, align="center")

# boxscore_pane = pn.widgets.Tabulator(boxscore, show_index=False, selectable=True, disabled=True)
# boxscore_pane.on_click(table_click_callback)
# main_row = pn.Row(plot_pane, boxscore_pane)

# date_picker.param.trigger('value')

################# serve the dashboard #################
# serve the simple app (no header)
pn.Column(
    filters_row, 
    pn.Row(plot_pane, sizing_mode='stretch_width'), 
    pn.Row(boxscore_pane, align="center"),
    align="center"
).servable()

# serve using the material template with SSA colors
# pn.template.MaterialTemplate(
#     site="SSA",
#     header_background='#305B5B',
#     title="Shot Chart Analyses",
#     # sidebar=[xaxis_widget, yaxis_widget, season_widget],
#     main=[pn.Column(filters_row, summary_row, main_row)], 
# ).servable()

###### multi page serve command
# panel serve panel_dashboard.py rink_dash.py --autoreload
