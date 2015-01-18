#! /usr/bin/env python3
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import os
import logging
import configparser
import traceback

# self-defined modules
from blindctrl.shared.stdscript import StandardScript
from blindctrl.sunpower.powercalc import PowerCalculator
from blindctrl.shared.opcclient import OpcClient


usage = """\
Usage: {name}

Based on the total sun power it derives the individual power of all windows. 
The window data is configured in the configuration file. The total power
is read from OPC or a file storage, depending on configuration.
"""


class SunPower(StandardScript):
    def __init__(self):
        # call parent constructor
        super().__init__()
        
        # setup OPC interface
        if self.config['OPC_STORAGE']['enabled']:
            self.opcclient = OpcClient(self.config['OPC_STORAGE']['url'], 
                                       self.config['OPC_STORAGE']['password'])
                                       
        # setup power calculator
        self.calculator = PowerCalculator(self.config)

        
    def process(self):
        try:
            # process effective angles
            self.calculator.process(self.config['WINDOWS'])
            
            # store power values
            if self.config['OPC_STORAGE']['enabled']:
                self.save_opc()
            if self.config['FILE_STORAGE']['enabled']:
                self.save_file()

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


    def save_opc(self):
        # store OPC requests
        opc_tags = []
        types = []
        values = []
        
        # setup values
        for i in range(len(self.config['WINDOWS'])):
            opc_tags.append(self.config['WINDOWS'][i]['opc']['power'])
            types.append('float')
            values.append(self.calculator.power_values[i])

        # write data to OPC
        self.opcclient.write(opc_tags, types, values)

    def save_file(self):
        config = configparser.ConfigParser()
        # read existing file data
        if os.path.isfile(self.config['FILE_STORAGE']['filename']):
            config.read(self.config['FILE_STORAGE']['filename'])
            
        # recreate data of this script
        config['sunpower'] = {}
        for i in range(len(self.config['WINDOWS'])):
            config['sunpower'][self.config['WINDOWS'][i]['name']] = \
                                        str(self.calculator.power_values[i])
                                        
        # save data file
        with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
            config.write(configfile)


if __name__ == "__main__":
    # init functionality
    sunpower = SunPower()

    if len(sys.argv) == 1:
        # derive all window power values
        sunpower.process()
    else:
        print(usage.format(name=sunpower.scriptname))
