"""This module provides utility functions used during application initialization."""

import os, os.path, shutil
import logging
import json


class StandardScript:
    def __init__(self):
        self.init_config()
        self.init_logging()


    def init_config(self):
        # ensure existing server config file
        filename = self._checkConfigFile()
        
        # read config file
        with open(filename) as config_file:
            self.config = json.load(config_file)


    def _checkConfigFile(self):
        # setup path for config files
        config_path = os.path.split(__file__)[0]
        configfile = os.path.join(config_path, "config.json")
    
        # check whether config file exists
        if not os.path.isfile(configfile):
            # check for template config file
            template_file = os.path.join(config_path, "config_json.tmpl")
            if not os.path.isfile(template_file):
                raise Exception("Neither config file nor template file found. Aborting.")

            # create template config file
            shutil.copyfile(template_file, configfile)
            raise Warning("Create empty configuration file. Please setup configuration and restart script.")

        # config file exists
        return configfile


    def init_logging(self):
        """setup logging to file and console"""
        # extract filename
        scriptname = os.path.splitext(os.path.basename(sys.argv[0]))[0]

        # setup root logger
        # we assume a higher log level on console logger
        logging.getLogger().setLevel(self.config['LOGGING']['log_level_console'].upper())

        # create file and console handler
        log_file = logging.FileHandler(os.path.join(config['log_dir'],
                                                    scriptname + '.log'))
        log_file.setLevel(self.config['LOGGING']['log_level_file'].upper())
        log_console = logging.StreamHandler()
        log_console.setLevel(self.config['LOGGING']['log_level_console'].upper())

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        log_file.setFormatter(formatter)

        # add the handlers to the logger
        logging.getLogger().addHandler(log_file)
        logging.getLogger().addHandler(log_console)

        #logging.getLogger().debug('logging started')
