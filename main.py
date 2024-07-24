from Bot import VkBot
from config.config import DATABASE, PATH
import os
from db import dbhandle, Model

if __name__ == '__main__':
    print('Starting...')
    try:
        os.system(f'rm {DATABASE}.sql {PATH + "media/temp/*"}')
    except:
        pass
    dbhandle.create_tables(Model.__subclasses__())
    VkBot().run()
