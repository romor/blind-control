#! /usr/bin/env python3
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import logging
import traceback
import time
import atexit
import RPi.GPIO as GPIO

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
    # time delay between invoking remote threads
    # this inhibits synchronous RF commands which conflicts with supply power
    REMOTE_THREAD_DELAY = 2    # seconds


    def __init__(self):
        # call parent constructor
        super().__init__()
        
        # initialize working classes
        self.state_ctrl = StateCtrl(self.config)
        
        # setup RPi
        # don't do this in RemoteDriver because this has multiple instances
        # use P1 header pin numbering convention
        GPIO.setmode(GPIO.BOARD)
        # reset all pins to inputs at exit
        atexit.register(GPIO.cleanup)


    def process(self, current_state = None, desired_state = None):
        try:
            # read desired state switches
            self.state_ctrl.get_switching_commands(current_state, desired_state)

            # are switching commands necessary?
            if len(self.state_ctrl.cmds):
                # determine remote commands
                command_ctrl = CommandCtrl(self.config)
                command_ctrl.derive_remote_commands(self.state_ctrl.cmds)

                # control remotes
                drivers_running = []
                for remote_cmds in command_ctrl.cmds:
                    remote_parameter = self.config['REMOTES'][remote_cmds['id']]
                    driver = RemoteDriver(remote_cmds['id'], remote_parameter, remote_cmds['cmds'])
                    # invoke background thread to control the remote
                    driver.start()
                    drivers_running.append(driver)

                    # delay to have next remote started acyclic
                    # to avoid same time RF commands
                    time.sleep(self.REMOTE_THREAD_DELAY)

                # wait until remote threads are finished
                for cur_thread in drivers_running:
                    cur_thread.join()

            else:
                logging.getLogger().debug("No switching necessary.")

            # store desired states
            # we do this even if we did not switch anything to initialize the storage if needed
            self.state_ctrl.store_new_states()

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise

        # return the number of executed remote commands
        return len(self.state_ctrl.cmds)


if __name__ == "__main__":
    # init functionality
    remote_ctrl = RemoteCtrl()

    if len(sys.argv) == 1:
        # derive all desired blind states
        remote_ctrl.process()
    else:
        print(usage.format(name=remote_ctrl.scriptname))
