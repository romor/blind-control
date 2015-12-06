#! /usr/bin/env python3
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import os
import logging
import datetime
import traceback
import configparser
import paho.mqtt.client as mqtt

# self-defined modules
from blindctrl.shared.stdscript import StandardScript
from blindctrl.zamg.mailparser import MailParser
from blindctrl.zamg.csvdecoder import CsvDecoder
from blindctrl.shared.opcclient import OpcClient


usage = """\
Usage: {name} [<filename>]

If <filename> is given, it parses the csv content and writes its data to the
datapoint.
If <filename> is not given, it fetches email from the configured email server and
downloads and processes all data files.
"""


class Zamg(StandardScript):
    def __init__(self):
        # call parent constructor
        super().__init__()

        # setup OPC interface
        if self.config['OPC_STORAGE']['enabled']:
            self.opcclient = OpcClient(self.config['OPC_STORAGE']['url'], 
                                       self.config['OPC_STORAGE']['password'])

        # setup mqtt connection
        if self.config['MQTT_STORAGE']['enabled']:
            self.mqtt = mqtt.Client()
            # quick and dirty: we assume to be connected before we finished email parsing...
            #self.mqtt.on_connect = self._on_mqtt_connect
            if 'user' in self.config['MQTT_STORAGE']:
                self.mqtt.username_pw_set(self.config['MQTT_STORAGE']['user'], 
                        self.config['MQTT_STORAGE']['password'])
            self.mqtt.connect(self.config['MQTT_STORAGE']['host'], self.config['MQTT_STORAGE']['port'])
            self.mqtt.loop_start()

        # setup data members
        self.data = None


    def process_csv(self, csv):
        try:
            decoder = CsvDecoder(self.config)
            decoder.decode(csv)

            # process data
            self.sun_today = 0
            
            # loop through data
            for row in decoder.data:
                # is this timestamp fitting?
                timediff = (row['date']-datetime.datetime.utcnow()).total_seconds()
                # is data not older than 1 hour?
                if timediff > -3600:
                    # sum minutes of remaining sun for today
                    if row['date'].date() == datetime.datetime.utcnow().date():
                        self.sun_today += row['sun']
                    
                    # is this the most recent timestamp?
                    if timediff <= 0:
                        # store this data row as our best guess
                        self.data = row

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


    def set_opc(self, temperature, sun):
        # setup values
        opc_tags = [self.config['OPC_STORAGE']['tag_temperature'], 
                    self.config['OPC_STORAGE']['tag_sunpower']]
        types = ['float', 'float']
        values = [temperature, sun]

        # write data to OPC
        self.opcclient.write(opc_tags, types, values)


    def set_file(self, temperature, sun):
        config = configparser.ConfigParser()
        # read existing file data
        if os.path.isfile(self.config['FILE_STORAGE']['filename']):
            config.read(self.config['FILE_STORAGE']['filename'])
            
        config[self.scriptname] = {}
        config[self.scriptname]['Temperature'] = str(temperature)
        config[self.scriptname]['SunPower'] = str(sun)
        with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
            config.write(configfile)


    def set_mqtt(self, temperature, sun, sun_today):
        # publish values to MQTT broker
        path = self.config['MQTT_STORAGE']['prefix']+"zamg"
        self.mqtt.publish(path+"/temperature", temperature, retain=True)
        self.mqtt.publish(path+"/sun", sun, retain=True)
        self.mqtt.publish(path+"/sun_today", sun_today)
        self.mqtt.publish(path+"/last_update", str(datetime.datetime.now()), retain=True)


    def process_mail(self):
        # check for entered configuration
        if len(self.config['EMAIL']['servername']) == 0:
            logging.getLogger().error("Please configure config file. Aborting.")
            return

        logging.getLogger().info("Retrieval from mail server " + self.config['EMAIL']['servername'])
        try:
            # setup mail parser
            mailparser = MailParser(self.config)
            mailparser.add_csvobserver(self.process_csv)
            # start retrieval
            mailparser.parse()

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())


    def process_data(self):
        # if retrieval succeeded we have valid data now
        if self.data:
            logging.getLogger().info("Set temperature: {}, sun: {:2f}"
                    .format(self.data['temperature'], self.data['sun']/60))

            # store temperature and sun power
            if self.config['OPC_STORAGE']['enabled']:
                self.set_opc(self.data['temperature'], self.data['sun']/60)
            if self.config['FILE_STORAGE']['enabled']:
                self.set_file(self.data['temperature'], self.data['sun']/60)
            if self.config['MQTT_STORAGE']['enabled']:
                self.set_mqtt(self.data['temperature'], self.data['sun']/60, self.sun_today)


def main():
    """main entry point"""
    # init functionality
    zamg = Zamg()
    # fetch csv files from email server
    zamg.process_mail()
    zamg.process_data()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # main entry point
        main()

    elif len(sys.argv) == 2:
        # init functionality
        zamg = Zamg()
        # parse file given on command line
        logging.getLogger().info("Importing file " + sys.argv[1])
        if os.path.isfile(sys.argv[1]):
            zamg.process_csv(open(sys.argv[1], 'rb').read().decode())
            zamg.process_data()
        else:
            logging.getLogger().error("Import file not found.")

    else:
        print(usage.format(name="zamg"))
