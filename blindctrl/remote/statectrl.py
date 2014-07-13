#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import os
import logging
import configparser

# self-defined modules


class StateCtrl:
    def __init__(self, config):
        # store configuration
        self.config = config

        # initialize data storage
        self.current_states = []
        self.desired_states = []
        self.cmds = []


    def get_switching_commands(self):
        # read current and desired states
        self.read_file()
            
        # determine switching commands
        for i in range(len(self.config['WINDOWS'])):
            if self.current_states[i] != self.desired_states[i]:
                # determine command type
                if self.desired_states[i]:
                    cmd = self.config['WINDOWS'][i]['down_cmd']
                else:
                    cmd = "up"
                # store command
                self.cmds.append({
                    'remote': self.config['WINDOWS'][i]['remote'],
                    'cmd': cmd,
                })


    def read_file(self):
        config = configparser.ConfigParser()
        config.read(self.config['FILE_STORAGE']['filename'])
        
        # clear data array, if already filled
        del self.current_states[:]
        del self.desired_states[:]
        
        for window in self.config['WINDOWS']:
            # process current states
            try:
                state = int(config['statectrl'][window['name']])
            except KeyError:
                state = 0
            self.current_states.append(state)
            
            # process desired states
            try:
                state = int(config['commander'][window['name']])
            except KeyError:
                logging.getLogger().error("No command state present for {}."\
                                .format(window['name']))
                state = 0
            self.desired_states.append(state)


    def store_new_states(self):
        config = configparser.ConfigParser()
        # read existing file data
        if os.path.isfile(self.config['FILE_STORAGE']['filename']):
            config.read(self.config['FILE_STORAGE']['filename'])

        # recreate data of this script
        config['statectrl'] = {}
        for i in range(len(self.config['WINDOWS'])):
            config['statectrl'][self.config['WINDOWS'][i]['name']] = \
                                        str(int(self.desired_states[i]))

        # save data file
        with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
            config.write(configfile)