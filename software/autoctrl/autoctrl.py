#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import logging
import os
import shutil
import configparser
import traceback
import datetime
import time

# self-defined modules
from opcclient import OpcClient
from sunpower import SunPower


scriptname = os.path.splitext(os.path.basename(__file__))[0]
configfile = scriptname + ".ini"

usage = """\
Usage: {name}

Perform automatic window rollo control.
""".format(name=scriptname)


class AutoCtrl:
    def __init__(self):
        # check for config file existance
        if not self.checkConfigFile():
            raise Exception("Config file error.")

        # setup config parser
        parser = configparser.ConfigParser()
        parser.read([configfile, "zamg.ini"])
        self.config = parser['DEFAULT']

        # setup OPC interface
        self.opcclient = OpcClient(self.config['opc.url'], self.config['opc.password'])

        # setup data members
        self.temperature_out = None
        self.temperature_in  = None
        self.sun             = None


    def checkConfigFile(self):
        # check whether config file exists
        if not os.path.isfile(configfile):
            # check for template config file
            templfile = scriptname + "_ini.tmpl"
            if not os.path.isfile(templfile):
                logging.getLogger().error("Neither config file nor template file found. Aborting.")
                return False

            # create template config file
            shutil.copyfile(templfile, configfile)
            logging.getLogger().warn("Created empty config file.")
            logging.getLogger().error("Please setup mail server before running this script.")
            return False

        # config file exists
        return True


    def get_zamg_data(self):
        opc_tags = [
            self.config['opc.tag_temperature'],
            self.config['opc.tag_sun'],
        ]
        values = self.opcclient.read(opc_tags)
        self.temperature_out = float(values[0])
        self.temperature_in  = 22.0 # TODO
        self.sun             = float(values[1])
        logging.getLogger().info("Temperature: {}; sun: {}".format(self.temperature_out, self.sun))


    def set_opc(self, windows):
        # set each window individually to avoid remote control channel conflicts
        for window in windows:
            # setup values
            opc_tags = []
            types = []
            values = []
            opc_tags.append(self.config['opc.tag_window_power'].format(window['opc_power']))
            types.append('float')
            values.append(window['power'])

            # write data to OPC
            self.opcclient.write(opc_tags, types, values)
            
            # add delay to allow LINX switching
            time.sleep(1.8)   # must be greater than 1 second (LINX schedule)
            
        # TODO: also derive power limit


    def process(self):
        # get opc data
        self.get_zamg_data()

        # derive window powers
        sun_power = SunPower()
        sun_power.process(self.sun)

        # store temperature, sun and powers to virtual input
        self.set_opc(sun_power.windows)


def setup_logging():
    logging.getLogger().setLevel(logging.INFO)

    # create file and console handler
    log_file = logging.FileHandler(scriptname + '.log')
    log_console = logging.StreamHandler()

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    log_file.setFormatter(formatter)

    # add the handlers to the logger
    logging.getLogger().addHandler(log_file)
    logging.getLogger().addHandler(log_console)


if __name__ == "__main__":
    # setup logger
    setup_logging()

    # init functionality
    auto_ctrl = AutoCtrl()

    if len(sys.argv) == 1:
        # fetch csv files from email server
        auto_ctrl.process()
    else:
        print(usage)
