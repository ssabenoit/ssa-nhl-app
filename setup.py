"""
setup.py

setup file to register the cache clearing and reloading on a daily cron schedule
"""
import panel as pn
from warm_cache import warm_cache 

def clear_caches():
    # clears the cache
    pn.state.clear_caches()

def schedule_tasks():
    # clear and refresh the cache every morning
    pn.state.schedule_task('clear_cache', clear_caches, cron='2 5 * * *')
    pn.state.schedule_task('load_cache', warm_cache, cron='10 5 * * *')
    print("Scheduled daily cache refresh tasks.")


if __name__ == "__main__":
    schedule_tasks()