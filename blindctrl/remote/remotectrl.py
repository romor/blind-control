#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import logging
import traceback

# self-defined modules
from blindctrl.shared.stdscript import StandardScript
from blindctrl.remote.statectrl import StateCtrl
from blindctrl.remote.cmdctrl import CommandCtrl
from blindctrl.remote.remotedriver import RemoteDriver


usage = """\
Usage: {name}

Derive switching commands and operates remote controls accordingly.
"""


class RemoteCtrl(StandardScript):
    def __init__(self):
        # call parent constructor
        super().__init__()
        
        # initialize working classes
        self.state_ctrl = StateCtrl(self.config)


    def process(self):
        try:
            # read desired state switches
            self.state_ctrl.get_switching_commands()

            # are switching commands necessary?
            if len(self.state_ctrl.cmds):
                # determine remote commands
                command_ctrl = CommandCtrl(self.config)
                command_ctrl.derive_remote_commands(self.state_ctrl.cmds)

                # control remotes
                for remote_cmds in command_ctrl.cmds:
                    remote_parameter = self.config['REMOTES'][remote_cmds['id']]
                    driver = RemoteDriver(remote_cmds['id'], remote_parameter)
                    driver.process_cmds(remote_cmds['cmds'])
                    
                # TODO: wait until remote threads are finished
                
            else:
                logging.getLogger().info("No switching necessary.")

            # store desired states
            # we do this even if we did not switch anything to initialize the storage if needed
            self.state_ctrl.store_new_states()

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


if __name__ == "__main__":
    # init functionality
    remote_ctrl = RemoteCtrl()

    if len(sys.argv) == 1:
        # derive all desired blind states
        remote_ctrl.process()
    else:
        print(usage.format(name=remote_ctrl.scriptname))
