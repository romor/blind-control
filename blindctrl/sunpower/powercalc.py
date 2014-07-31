#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import ephem
import datetime
import math


class PowerCalculator():
    MIN_ALTITUDE = 1
    ANGLE_LIMIT  = 80

    def __init__(self):
        self.power_values = []
        pass


    @staticmethod
    def get_sun_coordinates():
        # get sun position
        o = ephem.Observer()
        # Vienna: 48 degree north; 16 degree east
        o.lat, o.long, o.date = '48:13', '16:22', datetime.datetime.utcnow()
        sun = ephem.Sun(o)
        logging.getLogger().debug("sun azimuth: {}; altitude: {}".format(sun.az, sun.alt))
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


    def process(self, windows):
        # clear result array, if already filled
        del self.power_values[:]
        
        # get sun position
        sun = self.get_sun_coordinates()
        sun_coordinates = self.polar_to_euklid(sun.az, sun.alt)

        # loop through all windows
        for window in windows:
            # transform from polar to euklid coordinates
            window_coordinates = self.polar_to_euklid(window['geo']['az']*math.pi/180, 
                                                      window['geo']['alt']*math.pi/180)
            angle = self.get_angle(sun_coordinates, window_coordinates)

            # check for sun: must be visible and window angle OK
            if sun.alt > self.MIN_ALTITUDE*math.pi/180 and angle < self.ANGLE_LIMIT*math.pi/180:
                power = math.cos(angle)
            else:
                power = 0.0

            # store result
            self.power_values.append(power)
            # perform logging
            if power > 0:
                logging.getLogger().info("{}: angle: {:0.0f}, power: {:0.2f}".format(
                    window['name'], angle*180/math.pi, power))
            else:
                logging.getLogger().debug("{}: angle: {:0.0f}, power: {:0.2f}".format(
                    window['name'], angle*180/math.pi, power))

