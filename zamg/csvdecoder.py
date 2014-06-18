#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import csv
import datetime


class CsvDecoder():
    def __init__(self, config):
        self.config = config
        self.data = None


    def __parseInt(self, string):
        if len(string) > 0:
            return int(string)
        else:
            return None


    def __extractRowData(self, row):
        # convert data types
        data = {}
        data['date'] = datetime.datetime.strptime(row[0], "%Y%m%d") + \
                       datetime.timedelta(hours=int(row[1]))
        data['temperature'] = float(row[2])
        data['sun'] = int(row[3])
        return data


    def decode(self, csv_string):
        lines = csv_string.split('\r\n')
        count = 0
        self.data = []

        # decode file
        reader = csv.reader(lines, delimiter=";")
        for row in reader:
            # add row
            if len(row) == 4:
                self.data.append(self.__extractRowData(row))
                count += 1

        logging.getLogger().info("decoded data (" +
                            str(len(self.data)) + " lines)")

        return count
