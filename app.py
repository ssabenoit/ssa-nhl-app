"""
NHL case study
Benoit Cambournac

app.py
manage snowflake connection
"""
import snowflake.connector
import pandas as pd
import requests
import cairosvg
from PIL import Image
from io import BytesIO


class nhl_snowflake():

    def __init__(self):
        # create the connection
        self.conn = snowflake.connector.connect(
            user='ssanick',
            password='Southshore2024!',
            account='jp55454.us-east-2.aws',
            warehouse='DBT_WH',
            database='DBT_ANALYTICS',
            schema='PROD'
        )

    def get_reg_season_stats(self, type='regular', season='20242025'):

        # create a cursor and run the query
        cur = self.conn.cursor()
        if type == 'regular':
            query = f'select * from TEAM_SEASON_STATS_REGULAR where season = {season}'
        cur.execute(query)
        
        description = cur.description
        # pull and format the results into a df
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in description])

        for column in description:
            
            # reformat 'Decimal' Columns to floats
            if column[-2] is not None:
                if column[-2] > 0:
                    df[column[0]] = df[column[0]].astype(float)
                    # df[column[0]] = df[column[0]].apply(lambda x: float(x))
            
        # for i in [0, 1, -1]:
        #     df[df.columns[i]] = df[df.columns[i]].astype(str)
        
        # print(df.dtypes)
        cur.close()
        return df
    
    def scarpe_logos(self):

        cur = self.conn.cursor()
        cur.execute("select TEAM_ABV, LOGO_URL from TEAM_SEASON_STATS_REGULAR")
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])

        for idx, team in df.iterrows():
            
            if team['LOGO_URL'] is not None:
                # retrieve the image bytes
                img = requests.get(team['LOGO_URL'])

                # convert the image response to a png if it is not
                if img.headers['Content-Type'] == 'image/svg+xml':
                    png_bytes = cairosvg.svg2png(img.content)
                    image = Image.open(BytesIO(png_bytes))

                image.save(f"logos/{team['TEAM_ABV']}.png")
                # with open(f"logos/{team['TEAM_ABV']}.png", "wb") as file:
                #     file.write(image)
        
        cur.close()

    def get_stat_leaders(self, stat, season, order='desc'):
        
        # get all the teams ranked by the given stat
        cur = self.conn.cursor()
        cur.execute(f"select TEAM_ABV, LOGO_URL, {stat} from TEAM_SEASON_STATS_REGULAR where season = {season} order by {stat} {order}")
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])

        cur.close()
        return df
    
    def get_plays(self, game='2023020001', play_type=None, team=None, season='20232024'):

        # format the query
        # get the team (or whole league) occurence of certain plays over a certain season
        if team is not None:
            if team == 'all':
                query = f"select * from ALL_PLAYS where season = {season}"
            else:
                query = f"select * from ALL_PLAYS where play_team_abv = {team} and season = {season}"
                # (away_abv = '{team}' or home_abv = '{team}')
            
            # if play_type is not None and type(play_type) == str:
            #     query += f" and description = '{play_type}'"
            # else:
            #     query += f" and description in {play_type}"
            #     print(query)

        # select the plays for a given game
        else:
            query = f"select * from ALL_PLAYS where id = {game}"

        # add the play type filtering to the query (if applicable)
        if play_type is not None and type(play_type) == str:
            query += f" and description = '{play_type}'"
        else:
            query += f" and description in {play_type}"
            print(query)
        
        # create a cursor and retreive the plays
        cur  = self.conn.cursor()
        cur.execute(query)
        df = pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])
        return df

    def __del__(self):
        # close the snowflake connection
        self.conn.close()
        print('Connection Closed')  
  


# test_app = nhl_snowflake()
# print(test_app.get_reg_season_stats(season='20242025'))
# test_app.scarpe_logos()
