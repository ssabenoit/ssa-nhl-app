"""
warm_cache.py

setup script to pre load every input combination to the panel cache
"""
import panel as pn
from panel_dashboard import get_reg_season_stats, get_stat_leaders, get_stat_names, get_x_table, get_y_table, bars_with_icons, main_scatter

# Function that will be cached for dashboard use
# @cache
# def load_reg_stats(season):
    
#     # load the given season regular season stats
#     data = get_reg_season_stats(season)  
#     return data

def warm_cache():
    """ setup function to warm the cache with every input combination """

    # clear previously held caches
    # clear_caches()

    # all possible inputs
    seasons = ["20242025", "20232024"]  
    stats = get_stat_names() # gets stat names, also warms that cache
    formatted_stats = [stat.replace(' ', '_').upper() for stat in stats]
    
    asc_stats = ['Goals Against', 'Goals Against Average', 'Pim', 'Pim Per Game', 'Giveaways', 'Giveaways Per Game']
    asc_stats = [stat.replace(' ', '_').upper() for stat in asc_stats]
   
    orders = {stat: 'asc' if stat in asc_stats else 'desc' for stat in formatted_stats}

    for season in seasons:
        
        # load the reg_season_stats
        get_reg_season_stats(season)

        # load the season's goals/GA bar graphs
        bars_with_icons('GOALS', True, season)
        bars_with_icons('GOALS_AGAINST', False, season)

        for stat in formatted_stats:

            # load the stat leaders
            get_stat_leaders(stat, season, orders[stat])
            
            # load the table getting functions
            get_x_table(stat, season)
            get_y_table(stat, season)

            # load every y stat for the current x stat (for the main scatter plot)
            for second_stat in formatted_stats:

                if second_stat != stat:
                    main_scatter(stat, second_stat, season)


if __name__ == "__main__":
    warm_cache()
