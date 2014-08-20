#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import os
import logging
import configparser

# self-defined modules


class CommandCtrl:
    def __init__(self, config):
        # store configuration
        self.config = config
        # setup storage
        self.cmds = []


    def derive_remote_commands(self, switching_cmds):
        # clear potentially existing commands
        del self.cmds[:]
        # switching_cmds has following structure:
        # [ { 'remote', 'cmd' } ]

        # loop through all commands
        for cmd in switching_cmds:
            # prepare command
            new_cmd = {
                'channel': cmd['remote']['channel'],
                'cmd': cmd['cmd'],
            }
            
            # determine remote or create new one
            remote_id = self._get_remote(cmd['remote']['id'])
            
            # store command
            self._store_cmd(new_cmd, self.cmds[remote_id]['cmds'])


    def _get_remote(self, id):
        # determine remote
        remote_id = None
        for i in range(len(self.cmds)):
            if self.cmds[i]['id'] == id:
                remote_id = i

        # create new remote?
        if remote_id is None:
            self.cmds.append({
                'id': id,
                'cmds' : [],
            })
            remote_id = len(self.cmds)-1
    
        return remote_id

        
    def _store_cmd(self, cmd, existing_cmds):
        # determine command insert position
        insert_position = None
        for i in range(len(existing_cmds)):
            if existing_cmds[i]['channel'] > cmd['channel']:
                insert_position = i
                
        # store command
        if insert_position != None:
            existing_cmds.insert(insert_position, cmd)
        else:
            existing_cmds.append(cmd)
