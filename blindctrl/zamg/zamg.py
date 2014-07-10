#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

# standard modules
import sys, os

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
""".format(name=os.path.splitext(os.path.basename(sys.argv[0]))[0])


class Zamg(StandardScript):
    def __init__(self):
        # call parent constructor
        super().__init__()

        # setup data members
        self.data = None


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
        opcclient = OpcClient(self.config['OPC_STORAGE']['url'], self.config['OPC_STORAGE']['password'])

        # setup values
        opc_tags = [self.config['OPC_STORAGE']['tag_temperature'], 
                    self.config['OPC_STORAGE']['tag_sunpower']]
        types = ['float', 'float']
        values = [temperature, sun]

        # write data to OPC
        opcclient.write(opc_tags, types, values)


    def set_file(self, temperature, sun):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {}
        config['DEFAULT']['Temperature'] = temperature
        config['DEFAULT']['SunPower'] = sun
        with open(self.config['FILE_STORAGE']['filename'], 'w') as configfile:
          config.write(configfile)


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
            # store temperature, sun and powers to OPC server
            if self.config['OPC_STORAGE']['enabled']:
                self.set_opc(self.data['temperature'], self.data['sun']/60)
            if self.config['FILE_STORAGE']['enabled']:
                self.set_file(self.data['temperature'], self.data['sun']/60)


if __name__ == "__main__":
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
