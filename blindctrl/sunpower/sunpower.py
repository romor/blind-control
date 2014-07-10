#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import os, json


class SunPower():
    # windows = [
    # {
        # 'name':   'Jalousie Ost',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 4,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen Ost',
        # 'alt':    49,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 5,
        # 'power':  None,
    # },
    # {
        # 'name':   'Jalousie West',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 7,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen West',
        # 'alt':    49,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 6,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen Süd',
        # 'alt':    45,
        # 'az':     AZIMUTH_HOUSE+180,
        # 'opc_power': 8,
        # 'power':  None,
    # },
    # {
        # 'name':   'Terasse Süd',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+180,
        # 'opc_power': 9,
        # 'power':  None,
    # },
    # {
        # 'name':   'Dach Ost',
        # 'alt':    65,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 10,
        # 'power':  None,
    # },
    # {
        # 'name':   'Dach West',
        # 'alt':    65,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 11,
        # 'power':  None,
    # },
    # ]

    def __init__(self):
        # read configuration
        config_path = os.path.join(os.path.split(__file__)[0], os.pardir, "shared", "config.json")
        with open(config_path) as config_file:    
            self.config = json.load(config_file)

        # check for config file existance
        if not self.checkConfigFile():
            raise Exception("Config file error.")

        # setup config parser
        parser = configparser.ConfigParser()
        parser.read(configfile)
        self.config = parser['DEFAULT']


    def process(self, sun_power):
        # invoke PowerCalculator
