import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from app import nhl_snowflake
from PIL import Image
from io import BytesIO
import requests
import cairosvg


def get_stat_leaders(stat, season, order):

    # connect to the db and retrieve the stat leaders
    app = nhl_snowflake()
    stat_leaders = app.get_stat_leaders(stat=stat, season=season, order=order)

    return stat_leaders


def bars_with_icons(stat='GOALS', sort_desc=True, season='20232024'):

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

    print(reg_stats)

    # keep the 7 leaders and correctly sort the df
    # reg_stats = reg_stats.sort_values(by=[stat], ascending = not sort_desc).head(7).sort_values(by=[stat], ascending=sort_desc)
    reg_stats[stat] = reg_stats[stat].astype(int)
    reg_stats = reg_stats.head(7).sort_values(by=[stat], ascending=sort_desc)
    val = int(reg_stats[stat].max() * 0.05)

    print("final\n", reg_stats)

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

    # return fig
    fig.show()


# bars_with_icons()
# bars_with_icons('GOALS_AGAINST', False)
# bars_with_icons(season='2024-2025')
# bars_with_icons('GOALS_AGAINST', False, season='2024-2025')

# df = pd.read_csv('teams.csv')

# for idx, row in df.iterrows():
        
#     team = row['TEAM_ABV']
#     if team in ['UTA']:
    
# image = Image.open(f'logos/{team}.png')
image = requests.get(f'https://assets.nhle.com/logos/nhl/svg/UTA_light.svg')
image = cairosvg.svg2png(image.content)
image = Image.open(BytesIO(image))
# image = image.convert('RGB')
image.save(f'logos/UTA.webp', 'webp', lossless=True)

