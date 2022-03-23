__author__ = "songjiangshan"
__copyright__ = "Copyright (C) 2021 songjiangshan \n All Rights Reserved."
__license__ = ""
__version__ = "1.0"
#https://blog.csdn.net/rusi__/article/details/100122350

import logging
import datetime
format_color = '%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s'
stream_headler = logging.StreamHandler()

file_log_name = datetime.datetime.now().strftime('%Y_%m_%d-%H_%M_%S')

logging.basicConfig(level=logging.DEBUG,
                    format=format_color,
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler('uwb'+file_log_name+'.log',mode='a'),
                        stream_headler
                    ]
                    )


log_colors ={
    logging.DEBUG: "\033[1;34m",  # blue
    logging.INFO: "\033[1;32m",  # green
    logging.WARNING: "\033[1;35m",  # magenta
    logging.ERROR: "\033[1;31m",  # red
    logging.CRITICAL: "\033[1;41m",  # red reverted
}
for i in log_colors:
    logging.addLevelName( i, log_colors[i]+"%s\033[1;0m" % logging.getLevelName(i))


