#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys
import logging
import os
import shutil
import configparser
import traceback
import datetime
import configparser

# self-defined modules
from blindctrl.zamg.mailparser import MailParser
from blindctrl.zamg.csvdecoder import CsvDecoder
from blindctrl.shared.opcclient import OpcClient


scriptname = os.path.splitext(__file__)[0]
configfile = scriptname + ".ini"

usage = """\
Usage: {name} [<filename>]

If <filename> is given, it parses the csv content and writes its data to the
datapoint.
If <filename> is not given, it fetches email from the configured email server and
downloads and processes all data files.
""".format(name=scriptname)


class Zamg:
    def __init__(self):
        # check for config file existance
        if not self.checkConfigFile():
            raise Exception("Config file error.")

        # setup config parser
        parser = configparser.ConfigParser()
        parser.read(configfile)
        self.config = parser['DEFAULT']

        # setup data members
        self.data = None


    def checkConfigFile(self):
        # check whether config file exists
        if not os.path.isfile(configfile):
            # check for template config file
            templfile = scriptname + "_ini.tmpl"
            if not os.path.isfile(templfile):
                logging.getLogger().error("Neither config file nor template file found. Aborting.")
                return False

            # create template config file
            shutil.copyfile(templfile, configfile)
            logging.getLogger().warn("Created empty config file.")
            logging.getLogger().error("Please setup mail server before running this script.")
            return False

        # config file exists
        return True


    def process_csv(self, csv):
        try:
            decoder = CsvDecoder(self.config)
            decoder.decode(csv)

            # loop through data
            for row in decoder.data:
                # is this the current estimate?
                timediff = (row['date']-datetime.datetime.now()).total_seconds()
                if timediff > 0 and timediff <= 3600:
                    # store data as best guess
                    self.data = row

        except Exception as e:
            logging.getLogger().error(traceback.format_exc())
            raise


    def set_opc(self, temperature, sun):
        logging.getLogger().info("Set temperature: {}, sun: {:2f}".format(temperature, sun))

        # setup OPC interface
        opcclient = OpcClient(self.config['opc.url'], self.config['opc.password'])

        # setup values
        opc_tags = [self.config['opc.tag_temperature'], self.config['opc.tag_sun']]
        types = ['float', 'float']
        values = [temperature, sun]

        # write data to OPC
        opcclient.write(opc_tags, types, values)


    def set_file(self, temperature, sun):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {}
        config['DEFAULT']['Temperature'] = temperature
        config['DEFAULT']['SunPower'] = sun
        with open(self.config['opc.url'][len("file:"):], 'w') as configfile:
          config.write(configfile)


    def process_mail(self):
        # check for entered configuration
        if len(self.config['email.host']) == 0:
            logging.getLogger().error("Please configure config file "+configfile+". Aborting.")
            return

        logging.getLogger().info("Retrieval from mail server " + self.config['email.host'])
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
            # process data
            if self.config['opc.url'].startswith("file:"):
                # store temperature, sun and powers to OPC server
                self.set_opc(self.data['temperature'], self.data['sun']/60)
            else:
                self.set_file(self.data['temperature'], self.data['sun']/60)


def setup_logging():
    logging.getLogger().setLevel(logging.INFO)

    # create file and console handler
    log_file = logging.FileHandler(scriptname + '.log')
    log_console = logging.StreamHandler()

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    log_file.setFormatter(formatter)

    # add the handlers to the logger
    logging.getLogger().addHandler(log_file)
    logging.getLogger().addHandler(log_console)


if __name__ == "__main__":
    # setup logger
    setup_logging()

    # init functionality
    zamg = Zamg()

    if len(sys.argv) == 1:
        # fetch csv files from email server
        zamg.process_mail()
        zamg.process_data()

    elif len(sys.argv) == 2:
        # parse file given on command line
        logging.getLogger().info("Importing file " + sys.argv[1])
        if os.path.isfile(sys.argv[1]):
            zamg.process_csv(open(sys.argv[1], 'rb').read())
            zamg.process_data()
        else:
            logging.getLogger().error("Import file not found.")

    else:
        print(usage)
