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


usage = """\
Usage: {name}

Derive desired blind state based on the window power values.
"""


class Commander(StandardScript):
    def __init__(self):
        # call parent constructor
        super().__init__()
        
        # initialize data storage
        self.temperature_out
        self.sunpower
        self.power_values = []
        self.desired_states = []


    def process(self):
        try:
            # read power values
            # we just support file storage
            self.read_file()
            
            # clear result array, if already filled
            del self.desired_states[:]
            # process desired states
            for i in range(len(self.config['WINDOWS'])):
                desired_state = self._get_desired_state(self.power_values[i])
                self.desired_states.append(desired_state)
            
            # store desired states
            # we just support file storage
            self.save_file()

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


    def _get_desired_state(self, window_power):
        # for active blinding we need two conditions fullfilled:
        # (1) sun power is above threshold and (2) radiation angle is in suitable range
		# also include outside temperature?
        return (self.sunpower >= self.config['CONTROL']['weather_threshold']) && \
               (window_power >= self.config['CONTROL']['angle_threshold'])


    def read_file(self):
        config = configparser.ConfigParser()
        config.read(self.config['FILE_STORAGE']['filename'])

        self.temperature_out = float(config['zamg']['Temperature'])
        self.sunpower        = float(config['zamg']['SunPower'])

        # clear result array, if already filled
        del self.power_values[:]
        # process desired states
        for window in self.config['WINDOWS']:
            try:
                cur_power = float(config['sunpower'][window['name']])
            except KeyError:
                logging.getLogger().error("No power value present for {}."\
                                .format(window['name']))
                cur_power = 0
            self.power_values.append(cur_power)


    def save_file(self):
        config = configparser.ConfigParser()
        # read existing file data
        if os.path.isfile(self.config['FILE_STORAGE']['filename']):
            config.read(self.config['FILE_STORAGE']['filename'])
            
        # recreate data of this script
        config[self.scriptname] = {}
        for i in range(len(self.config['WINDOWS'])):
            config[self.scriptname][self.config['WINDOWS'][i]['name']] = \
                                        str(int(self.desired_states[i]))

        # save data file
        with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
            config.write(configfile)


if __name__ == "__main__":
    # init functionality
    commander = Commander()

    if len(sys.argv) == 1:
        # derive all desired blind states
        commander.process()
    else:
        print(usage.format(name=commander.scriptname))
