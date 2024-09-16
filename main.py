from Bot import VkBot
from config.config import DATABASE, PATH
import os
from db import dbhandle, Model
from load_messages import load

if __name__ == '__main__':
    print('Starting...')
    try:
        os.system(f'rm {DATABASE}.sql {PATH + "media/temp/*"}')
    except:
        pass
    print('Creating tables...')
    dbhandle.create_tables(Model.__subclasses__())
    print('Loading messages...')
    load()
    print('Starting the bot...')
    VkBot().run()
