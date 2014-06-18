#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

import logging
import ephem
import datetime
import math


class SunPower():
    AZIMUTH_HOUSE = -16.5
    # altitude unten: 45, oben: 37.5, Dach: 25

    windows = [
    {
        'name':   'Jalousie Ost',
        'alt':    0,
        'az':     AZIMUTH_HOUSE+90,
        'opc_power': 4,
        'power':  None,
    },
    {
        'name':   'Rollladen Ost',
        'alt':    49,
        'az':     AZIMUTH_HOUSE+90,
        'opc_power': 5,
        'power':  None,
    },
    {
        'name':   'Jalousie West',
        'alt':    0,
        'az':     AZIMUTH_HOUSE+270,
        'opc_power': 7,
        'power':  None,
    },
    {
        'name':   'Rollladen West',
        'alt':    49,
        'az':     AZIMUTH_HOUSE+270,
        'opc_power': 6,
        'power':  None,
    },
    {
        'name':   'Rollladen Süd',
        'alt':    45,
        'az':     AZIMUTH_HOUSE+180,
        'opc_power': 8,
        'power':  None,
    },
    {
        'name':   'Terasse Süd',
        'alt':    0,
        'az':     AZIMUTH_HOUSE+180,
        'opc_power': 9,
        'power':  None,
    },
    {
        'name':   'Dach Ost',
        'alt':    65,
        'az':     AZIMUTH_HOUSE+90,
        'opc_power': 10,
        'power':  None,
    },
    {
        'name':   'Dach West',
        'alt':    65,
        'az':     AZIMUTH_HOUSE+270,
        'opc_power': 11,
        'power':  None,
    },
    ]

    MIN_ALTITUDE = 10
    ANGLE_LIMIT  = 80

    def __init__(self):
        pass


    def process(self, sun_minutes):
        # get sun position
        o = ephem.Observer()
        # Vienna: von 48 degree north; 16 degree east
        o.lat, o.long, o.date = '48:13', '16:22', datetime.datetime.utcnow()
        sun = ephem.Sun(o)
        logging.getLogger().info("sun azimuth: {}; altitude: {}".format(sun.az, sun.alt))
        # transform from polar to euklid coordinates
        sun_coordinates = [
            math.cos(sun.alt)*math.cos(sun.az),
            math.cos(sun.alt)*math.sin(sun.az),
            math.sin(sun.alt)
        ]

        for window in self.windows:
            # transform from polar to euklid coordinates
            window_coordinates = [
                math.cos(window['alt']*math.pi/180)*math.cos(window['az']*math.pi/180),
                math.cos(window['alt']*math.pi/180)*math.sin(window['az']*math.pi/180),
                math.sin(window['alt']*math.pi/180)
            ]
            # determine dot product (Skalarprodukt)
            cos_phi = 0
            for i in range(3):
                cos_phi += window_coordinates[i]*sun_coordinates[i]
            # dot product = length(vector1)+length(vector2)*cos(phi)
            angle = math.acos(cos_phi)

            # check for sun: must be visible and window angle OK
            if sun.alt > self.MIN_ALTITUDE*math.pi/180 and angle < self.ANGLE_LIMIT*math.pi/180:
                power = cos_phi * sun_minutes
            else:
                power = 0.0

            # finished power calculation
            window['power'] = power
            logging.getLogger().info("{}: angle: {:0.0f}, power: {:0.2f}".format(
                    window['name'], angle*180/math.pi, power))
