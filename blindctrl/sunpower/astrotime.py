#! /usr/bin/env python3
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import logging
import traceback
import datetime
import ephem

# self-defined modules
from blindctrl.shared.stdscript import StandardScript
from blindctrl.shared.opcclient import OpcClient


usage = """\
Usage: {name}

Sets the time of local sunset to an OPC data point.
"""


class Astrotime(StandardScript):
    HORIZON = '-7'    # -6=civil twilight

    def __init__(self):
        # call parent constructor
        super().__init__()
        
        # setup OPC interface
        if not self.config['OPC_STORAGE']['enabled']:
            raise Exception("Astrotime needs OPC storage enabled")
        self.opcclient = OpcClient(self.config['OPC_STORAGE']['url'], 
                                   self.config['OPC_STORAGE']['password'])


    def process(self):
        try:
            # determine sunset
            # get sun position
            o = ephem.Observer()
            # Vienna: 48 degree north; 16 degree east
            o.lat, o.long, o.date = '48:13', '16:22', datetime.datetime.utcnow()
            o.horizon = self.HORIZON
            sunset = ephem.localtime(o.next_setting(ephem.Sun()))
            logging.getLogger().info("Setting sunset to {}".format(sunset.strftime("%H:%M:%S")))
            
            # store to OPC data point
            self.save_opc(sunset)

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


    def save_opc(self, sunset):
        # setup values
        opc_tags = [self.config['OPC_STORAGE']['tag_sunset']]
        types = ['float']
        values = [sunset.hour*3600 + sunset.minute*60 + sunset.second]

        # write data to OPC
        self.opcclient.write(opc_tags, types, values)


if __name__ == "__main__":
    # init functionality
    astrotime = Astrotime()

    if len(sys.argv) == 1:
        # derive time
        astrotime.process()
    else:
        print(usage.format(name=astrotime.scriptname))
