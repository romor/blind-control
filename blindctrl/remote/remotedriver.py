#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import logging

# self-defined modules


class RemoteDriver:
    def __init__(self, remote_name, remote_config):
        # store configuration
        self.remote_name = remote_name
        self.remote_config = remote_config


    def process_cmds(self, cmds):
        # cmds has following format: 
        # [ { 'channel', 'cmd' } ] where cmd of ('up', 'down', 'my')
        for cur_cmd in cmds:
            logging.getLogger().info("Remote {}: channel {} {}".format(
                    self.remote_name, cur_cmd['channel'], cur_cmd['cmd']))
