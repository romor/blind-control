#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import ephem
import datetime
import math
import os, json


class SunPower():
    # windows = [
    # {
        # 'name':   'Jalousie Ost',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 4,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen Ost',
        # 'alt':    49,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 5,
        # 'power':  None,
    # },
    # {
        # 'name':   'Jalousie West',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 7,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen West',
        # 'alt':    49,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 6,
        # 'power':  None,
    # },
    # {
        # 'name':   'Rollladen Süd',
        # 'alt':    45,
        # 'az':     AZIMUTH_HOUSE+180,
        # 'opc_power': 8,
        # 'power':  None,
    # },
    # {
        # 'name':   'Terasse Süd',
        # 'alt':    0,
        # 'az':     AZIMUTH_HOUSE+180,
        # 'opc_power': 9,
        # 'power':  None,
    # },
    # {
        # 'name':   'Dach Ost',
        # 'alt':    65,
        # 'az':     AZIMUTH_HOUSE+90,
        # 'opc_power': 10,
        # 'power':  None,
    # },
    # {
        # 'name':   'Dach West',
        # 'alt':    65,
        # 'az':     AZIMUTH_HOUSE+270,
        # 'opc_power': 11,
        # 'power':  None,
    # },
    # ]

    MIN_ALTITUDE = 10
    ANGLE_LIMIT  = 80

    def __init__(self):
        # read configuration
        config_path = os.path.join(os.path.split(__file__)[0], "shared", "config.json")
        with open(config_path) as config_file:    
            self.config = json.load(config_file)


    @staticmethod
    def get_sun_coordinates():
        # get sun position
        o = ephem.Observer()
        # Vienna: 48 degree north; 16 degree east
        o.lat, o.long, o.date = '48:13', '16:22', datetime.datetime.utcnow()
        sun = ephem.Sun(o)
        logging.getLogger().info("sun azimuth: {}; altitude: {}".format(sun.az, sun.alt))
        # transform from polar to euklid coordinates
        return sun
        
    @staticmethod
    def polar_to_euklid(azimuth, altitude):
        return [
            math.cos(altitude)*math.cos(azimuth),
            math.cos(altitude)*math.sin(azimuth),
            math.sin(altitude)
        ]
        
    @staticmethod
    def get_angle(v1, v2):
        # we assume that the lengths of v1 and v2 are 1!
        # determine dot product (Skalarprodukt)
        cos_phi = 0
        for i in range(3):
            cos_phi += v1[i]*v2[i]
        # dot product = length(vector1)+length(vector2)*cos(phi)
        angle = math.acos(cos_phi)
        return angle


    def process(self, sun_minutes):
        # result array
        power_values = []
        
        # get sun position
        sun = self.get_sun_coordinates()
        sun_coordinates = self.polar_to_euklid(sun.az, sun.alt)

        # loop through all windows
        for window in self.config["WINDOWS"]:
            # transform from polar to euklid coordinates
            window_coordinates = self.polar_to_euklid(window['geo']['az'], window['geo']['alt'])
            angle = self.get_angle(sun_coordinates, window_coordinates)

            # check for sun: must be visible and window angle OK
            if sun.alt > self.MIN_ALTITUDE*math.pi/180 and angle < self.ANGLE_LIMIT*math.pi/180:
                power = cos_phi * sun_minutes
            else:
                power = 0.0

            # store result
            power_values.append(power)
            logging.getLogger().info("{}: angle: {:0.0f}, power: {:0.2f}".format(
                    window['name'], angle*180/math.pi, power))

        return power_values
