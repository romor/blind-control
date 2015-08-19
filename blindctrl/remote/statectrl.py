#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import os
import logging
import configparser

# self-defined modules
from blindctrl.shared.opcclient import OpcClient


class StateCtrl:
    def __init__(self, config):
        # store configuration
        self.config = config

        # read current blind states
        self.current_states = self._read_current_state()

        # initialize data storage
        self.desired_states = []
        self.cmds = []
        

    def get_switching_commands(self, desired_state = None):
        if desired_state is None:
            # read desired states from file or OPC
            if self.config['OPC_STORAGE']['enabled']:
                self.desired_states = self._read_opc()
            else:
                self.desired_states = self._read_desired_state()
        else:
            # take commands provided via parameter
            self.desired_states = desired_state
        assert len(self.current_states) == len(self.desired_states) == len(self.config['WINDOWS'])

        # clear switching commands, if already set
        del self.cmds[:]

        # determine switching commands
        for i in range(len(self.config['WINDOWS'])):
        
            # switching necessary?
            if self.desired_states[i] is not None and \
                    self.current_states[i] != self.desired_states[i]:
                window_cfg = self.config['WINDOWS'][i]
                
                # determine command type
                if self.desired_states[i]:
                    # down command
                    if 'down_cmd' in window_cfg:
                        cmd = window_cfg['down_cmd']
                    else:
                        cmd = "down"
                else:
                    # up command
                    if 'up_cmd' in window_cfg:
                        cmd = window_cfg['up_cmd']
                    else:
                        cmd = "up"
                
                # command may be disabled by config file
                if cmd is not None:
                    logging.getLogger().info("Switching {} to {}.".format(
                            window_cfg['name'], cmd))
                    # store command
                    self.cmds.append({
                        'remote': window_cfg['remote'],
                        'cmd': cmd,
                    })
                else:
                    logging.getLogger().info("Skipping command for {}.".format(window_cfg['name']))


    def _read_current_state(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config['FILE_STORAGE']['filename'])
        except configparser.ParsingError as e:
            logging.getLogger().error("Error parsing file storage: " + str(e))

        # create data array
        current_states = []
        
        for window in self.config['WINDOWS']:
            # process current states
            try:
                state = int(config['statectrl'][window['name']])
            except KeyError:
                state = 0
            current_states.append(state)

        return current_states


    def _read_desired_states(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config['FILE_STORAGE']['filename'])
        except configparser.ParsingError as e:
            logging.getLogger().error("Error parsing file storage: " + str(e))

        # create data array
        desired_states = []
        
        for window in self.config['WINDOWS']:
            # process desired states
            try:
                state = int(config['commander'][window['name']])
            except KeyError:
                # this is an error only if we use file commands, not OPC
                if not self.config['OPC_STORAGE']['enabled']:
                    logging.getLogger().error("No command state present for {}."\
                                .format(window['name']))
                state = 0
            desired_states.append(state)
        
        return desired_states


    def _read_opc(self):
        desired_states = []
        opcclient = OpcClient(self.config['OPC_STORAGE']['url'],
                              self.config['OPC_STORAGE']['password'])
        opc_tags = [
            self.config['OPC_STORAGE']['tag_control'],
        ]
        values = opcclient.read(opc_tags)
        value = values[0]

        for i in range(len(self.config['WINDOWS'])):
            # process current state
            ctrl_id = self.config['WINDOWS'][i]['opc']['ctrl']
            try:
                state = int(value[2*ctrl_id:2*ctrl_id+2])
            except KeyError:
                logging.getLogger().error("Error getting state for window {}, {}"\
                        .format(ctrl_id, self.config['WINDOWS'][i]['name']))
                state = 0
            desired_states.append(state)
        
        return desired_states


    def store_desired_states(self):
        # update class member
        has_changed = False
        for i in range(len(self.config['WINDOWS'])):
            if self.desired_states[i] is not None and \
                    self.current_states[i] != self.desired_states[i]:
                has_changed = True
                self.current_states[i] = self.desired_states[i]
        
        if has_changed:
            # update file storage
            config = configparser.ConfigParser()
            # read existing file data
            if os.path.isfile(self.config['FILE_STORAGE']['filename']):
                try:
                    config.read(self.config['FILE_STORAGE']['filename'])
                except configparser.ParsingError as e:
                    logging.getLogger().error("Error parsing file storage: " + str(e))

            # recreate data of this script
            config['statectrl'] = {}
            for i in range(len(self.config['WINDOWS'])):
                if self.current_states[i] != self.desired_states[i]:
                    has_changed = True
                    # store class member
                    self.current_states[i] = self.desired_states[i]

                # store in file
                config['statectrl'][self.config['WINDOWS'][i]['name']] = \
                                            str(int(self.desired_states[i]))

            # save data file
            with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
                config.write(configfile)
