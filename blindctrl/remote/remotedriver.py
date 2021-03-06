#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import logging
import time
import RPi.GPIO as GPIO
import threading 

# self-defined modules


class RemoteDriver(threading.Thread):
    # Somfy Telis 4 has 5 channels
    NR_CHANNELS = 5
    
    # timeout after which remote channel flashing has gone
    CHANNEL_TIMEOUT = 6     # seconds
    
    # time interval for normal button presses
    BUTTON_HOLD    = 0.1    # seconds
    BUTTON_TIMEOUT = 0.2    # seconds

    
    def __init__(self, remote_name, remote_config, cmds):
        # call parent's constructor
        super().__init__()
        
        # store configuration
        self.remote_name = remote_name
        self.remote_config = remote_config
        self.commands = cmds
        
        # initialize remote
        self.cur_channel = 0
        

    def run(self):
        # cmds has following format: 
        # [ { 'channel', 'cmd' } ] where cmd of ('up', 'down', 'my')
        
        for cur_cmd in self.commands:
            # process command
            logging.getLogger().debug("Remote {}: channel {} {}".format(
                    self.remote_name, cur_cmd['channel'], cur_cmd['cmd']))
            self.set_channel(cur_cmd['channel'])
            self.invoke_cmd(cur_cmd['cmd'])

        # reset channel
        self.set_channel(0)

        
    def set_channel(self, channel):
        # do we need to switch?
        if self.cur_channel != channel:
            # it will then output low level, which equals a button press
            logging.getLogger().debug("Set channel to {}.".format(channel))
            # how many channels to switch? this works also fine for negative numbers
            channel_diff = (channel - self.cur_channel) % self.NR_CHANNELS
            # we need 1 press more than the channel difference
            for i in range(channel_diff+1):
                self.switch_pin(self.remote_config['channel'])
            # after channel switching wait until channel flashing is over
            time.sleep(self.CHANNEL_TIMEOUT)
            # store new channel
            self.cur_channel = channel

            
    def invoke_cmd(self, cmd):
        # the command may be disabled
        if cmd:
            logging.getLogger().debug("Invoke cmd {}.".format(cmd))
            self.switch_pin(self.remote_config[cmd])


    def switch_pin(self, pin_nr):
        try:
            # Pin ON
            # to turn a button on we just need to set the GPIO to output
            # it will then output low level, which equals a button press
            logging.getLogger().debug("{} pin {}: ON".format(self.remote_name, pin_nr))
            GPIO.setup(pin_nr, GPIO.OUT)
            # delay
            time.sleep(self.BUTTON_HOLD)

            # Pin OFF
            # accordingly, to turn a button of we configure the GPIO to input
            # the high impetance state equals no button press
            logging.getLogger().debug("{} pin {}: OFF".format(self.remote_name, pin_nr))
            GPIO.setup(pin_nr, GPIO.IN)
            # delay
            time.sleep(self.BUTTON_TIMEOUT)
        except RuntimeError as ex:
            logging.getLogger().error("Error controlling GPIOs: " + str(ex))
