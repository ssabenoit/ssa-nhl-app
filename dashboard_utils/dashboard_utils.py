import panel as pn
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from app import nhl_snowflake
from PIL import Image
from io import BytesIO
import requests
import cairosvg
# import snowflake.connector


@pn.cache
def get_reg_season_stats(season='20242025'):
    ''' cached function that pulls regular season stats from the Db for the given season
    (should only need to call against db once per different season) '''

    # access the database and return the regular season stats
    app = nhl_snowflake()
    reg_stats = app.get_reg_season_stats(season=season)

    return reg_stats

@pn.cache
def get_stat_leaders(stat, season, order):

    # connect to the db and retrieve the stat leaders
    app = nhl_snowflake()
    stat_leaders = app.get_stat_leaders(stat=stat, season=season, order=order)

    return stat_leaders

@pn.cache
def main_scatter(x_stat=None, y_stat=None, season=None):
    ''' creates the main scatter plot of the two given stats accross all 32 NHL teams with each 
    team logo as the scatter point identifier '''

    if x_stat is None and y_stat is None:
        return go.Figure()
    
    # reformatting the stats and season strings
    x_stat_col = x_stat.replace(' ', '_').upper()
    y_stat_col = y_stat.replace(' ', '_').upper()
    season_val = season.replace('-', '')


    # app = nhl_snowflake()
    # reg_stats = app.get_reg_season_stats(season=season_val)
    reg_stats = get_reg_season_stats(season=season_val)

    fig = px.scatter(reg_stats, x=x_stat_col, y=y_stat_col, hover_name='TEAM_ABV',
                     labels={x_stat_col: x_stat, y_stat_col: y_stat}, template="simple_white")
    fig.add_vline(x=reg_stats[x_stat_col].mean(), line_dash='dash', line_color='blue', opacity=0.5, line_width=2)
    fig.add_hline(y=reg_stats[y_stat_col].mean(), line_dash='dash', line_color='blue', opacity=0.5, line_width=2)

    # determining image size based on the range of field values
    img_width = (reg_stats[x_stat_col].max() - reg_stats[x_stat_col].min()) * 0.1
    img_height = (reg_stats[y_stat_col].max() - reg_stats[y_stat_col].min()) * 0.1

    # add the logo for each team over its corresponding data point
    for idx, row in reg_stats.iterrows():
    
        if row['LOGO_URL'] is not None:
            # retrieve the image bytes
            img = requests.get(row['LOGO_URL'])

            # convert the image response to a png if it is not
            if img.headers['Content-Type'] == 'image/svg+xml':
                img = cairosvg.svg2png(img.content)

            # add the image on top of the points
            fig.add_layout_image(
                x=row[x_stat_col],
                y=row[y_stat_col],
                source=Image.open(BytesIO(img)),
                xref="x",
                yref="y",
                sizex=img_width,
                sizey=img_height,
                sizing='contain',
                xanchor="center",
                yanchor="middle",
            )
    
    fig.update_layout(
        height=800
    )
    
    return fig

@pn.cache
def bars_with_icons(stat='GOALS', sort_desc=True, season=None):

    # reformat the passed season string
    season_val = season.replace('-', '')
    if sort_desc: order='desc'
    else: order='asc'

    # get each teams' stats
    # app = nhl_snowflake()
    # reg_stats = app.get_stat_leaders(stat=stat, season=season_val, order=order)
    # print(reg_stats)

    # get the stat leaders
    reg_stats = get_stat_leaders(stat=stat, season=season_val, order=order)

    # pull in each teams color
    colors = pd.read_csv('teams.csv')
    reg_stats = reg_stats.merge(colors, on=['TEAM_ABV'], how='left')

    # keep the 7 leaders and correctly sort the df
    # reg_stats = reg_stats.sort_values(by=[stat], ascending = not sort_desc).head(7).sort_values(by=[stat], ascending=sort_desc)
    reg_stats = reg_stats.head(7).sort_values(by=[stat], ascending=sort_desc)
    val = int(reg_stats[stat].max() * 0.15)

    # fig = px.scatter(reg_stats, x=x_stat, y=y_stat, hover_name='TEAM_ABV')
    fig = px.bar(reg_stats, y='TEAM_ABV', x=stat, orientation='h', opacity=0.2, color='color_hex',
                 color_discrete_sequence=list((reg_stats['color_hex'])), template="simple_white")

    # add the logos as icons to the end of each bar
    for idx, row in reg_stats.iterrows():
    
        if row['LOGO_URL'] is not None:
            # print(row['TEAM_ABV'])
            if row['TEAM_ABV'] == 'UTA':
                # retrieve the image bytes
                img = requests.get(row['LOGO_URL'])

                # convert the image response to a png if it is not
                if img.headers['Content-Type'] == 'image/svg+xml':
                    img = cairosvg.svg2png(img.content)
                    img = BytesIO(img)
            else:
                img = f"logos/{row['TEAM_ABV']}.png"

            # add the image on top of the points
            fig.add_layout_image(
                x=row[stat],
                y=row['TEAM_ABV'],
                source=Image.open(img),
                # source=Image.open(BytesIO(img)),
                xref="x",
                yref="y",
                sizex=val,
                sizey=val,
                sizing='contain',
                xanchor="center",
                yanchor="middle",
            )
    
    fig.update_layout(
        height=350,
        # width=1200,
        bargap=0.55,
        title_text=f"{stat.replace('_', ' ').title()} Leaders", 
        title_x=0.5,
        showlegend=False
    )

    fig.update_yaxes(showticklabels=False, title='')
    fig.update_xaxes(title='')

    return fig

@pn.cache
def get_stat_names():
    ''' retrieves all the stat names necessary for the dropdowns and overall dash'''

    # get all the stats in the season stats table
    reg_stats = get_reg_season_stats()

    # pull and format the stat strings
    stats = list(reg_stats.columns[4:-1])
    formatted_stats = [stat.replace('_', ' ').title() for stat in stats]

    return formatted_stats

@pn.cache
def get_x_table(x_stat = None, season=None):
    ''' retrieves the team rankings of the given stat '''
    if x_stat is not None:

        # reformatting the stat identifier string
        if x_stat in ['Goals Against', 'Goals Against Average', 'Pim', 'Pim Per Game', 
                      'Giveaways', 'Giveaways Per Game']:
            order_by = 'asc'
        else: order_by = 'desc'

        season_val = season.replace('-', '')

        # get the season stats  
        # app = nhl_snowflake()
        # leaders = app.get_stat_leaders(x_stat.replace(' ', '_').upper(), season=season_val, order=order_by)
        leaders = get_stat_leaders(x_stat.replace(' ', '_').upper(), season=season_val, order=order_by)

        columns = [label.replace('_', ' ').title() for label in list(leaders.columns)]
        columns[0] = 'Team'
        leaders.columns = columns 
        leaders.index = [i for i in range(1,len(leaders)+1)]
        leaders = leaders[['Team', x_stat]]

        return leaders

@pn.cache 
def get_y_table(y_stat = None, season=None):
    ''' same as get_x_table -- can propbably be deprecated '''

    return get_x_table(y_stat, season)
    # if y_stat is not None:

    #     # get the season stats and reformatting the stat string
    #     app = nhl_snowflake()

    #     season_val = season.replace('-', '')
    #     leaders = app.get_stat_leaders(y_stat.replace(' ', '_').upper(), season=season_val)

    #     columns = [label.replace('_', ' ').title() for label in list(leaders.columns)]
    #     columns[0] = 'Team'
    #     leaders.columns = columns 
    #     leaders.index = [i for i in range(1,len(leaders)+1)]

    #     return leaders
