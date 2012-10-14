# This file is part of pyRFXtrx, a Python library to communicate with
# the RFXtrx family of devices from http://www.rfxcom.com/
# See https://github.com/woudt/pyRFXtrx for the latest version.
#
# Copyright (C) 2012  Edwin Woudt <edwin@woudt.nl>
#
# pyRFXtrx is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyRFXtrx is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pyRFXtrx.  See the file COPYING.txt in the distribution.
# If not, see <http://www.gnu.org/licenses/>.

import lowlevel


###############################################################################
# RFXtrxTransport class
###############################################################################

class RFXtrxTransport(object):
    """ Abstract superclass for all transport mechanisms """

    def parse(self, data):
        pkt = lowlevel.parse(data)
        if pkt is not None:
            if isinstance(pkt, lowlevel.SensorPacket):
                return SensorEvent(pkt)
            else:
                return ControlEvent(pkt)


###############################################################################
# RFXtrxDevice class
###############################################################################

class RFXtrxDevice(object):
    """ Superclass for all devices """

    def __init__(self, pkt):
        """Constructor"""
        self.packettype = pkt.packettype
        self.subtype = pkt.subtype
        self.type_string = pkt.type_string
        self.id_string = pkt.id_string

    def __eq__(self, other):
        if self.packettype != other.packettype:
            return False
        if self.subtype != other.subtype:
            return False
        return self.id_string == other.id_string

    def __str__(self):
        return "{0} type='{1}' id='{2}'".format(
            type(self), self.type_string, self.id_string)


###############################################################################
# LightingDevice class
###############################################################################

class LightingDevice(RFXtrxDevice):
    """ Concrete class for a lighting device """

    def __init__(self, pkt):
        super(LightingDevice, self).__init__(pkt)
        if isinstance(pkt, lowlevel.Lighting1):
            self.housecode = pkt.housecode
            self.unitcode = pkt.unitcode
        if isinstance(pkt, lowlevel.Lighting2):
            self.id_combined = pkt.id_combined
            self.unitcode = pkt.unitcode
        if isinstance(pkt, lowlevel.Lighting3):
            self.system = pkt.system
            self.channel = pkt.channel

    def send_on(self, transport):
        if self.packettype == 0x10:  # Lighting1
            pkt = lowlevel.Lighting1()
            pkt.set_transmit(self.subtype, 0, self.housecode, self.unitcode,
                             0x01)
            transport.send(pkt.data)
        elif self.packettype == 0x11:  # Lighting2
            pkt = lowlevel.Lighting2()
            pkt.set_transmit(self.subtype, 0, self.id_combined, self.unitcode,
                             0x01, 0x00)
            transport.send(pkt.data)
        elif self.packettype == 0x12:  # Lighting3
            pkt = lowlevel.Lighting3()
            pkt.set_transmit(self.subtype, 0, self.system, self.channel,
                             0x10)
            transport.send(pkt.data)
        else:
            raise ValueError("Unsupported packettype")

    def send_off(self, transport):
        if self.packettype == 0x10:  # Lighting1
            pkt = lowlevel.Lighting1()
            pkt.set_transmit(self.subtype, 0, self.housecode, self.unitcode,
                             0x00)
            transport.send(pkt.data)
        elif self.packettype == 0x11:  # Lighting2
            pkt = lowlevel.Lighting2()
            pkt.set_transmit(self.subtype, 0, self.id_combined, self.unitcode,
                             0x00, 0x00)
            transport.send(pkt.data)
        elif self.packettype == 0x12:  # Lighting3
            pkt = lowlevel.Lighting3()
            pkt.set_transmit(self.subtype, 0, self.system, self.channel,
                             0x1a)
            transport.send(pkt.data)
        else:
            raise ValueError("Unsupported packettype")

    def send_dim(self, transport, level):
        if self.packettype == 0x10:  # Lighting1
            raise ValueError("Dim level unsupported for Lighting1")
            # Supporting a dim level for X10 directly is not possible because
            # RFXtrx does not support sending extended commands
        elif self.packettype == 0x11:  # Lighting2
            pkt = lowlevel.Lighting2()
            pkt.set_transmit(self.subtype, 0, self.id_combined, self.unitcode,
                             0x02, (level + 6) * 15 / 100)
            transport.send(pkt.data)
        elif self.packettype == 0x12:  # Lighting3
            raise ValueError("Dim level unsupported for Lighting3")
            # Should not be too hard to add dim level support for Lighting3
            # (Ikea Koppla) due to the availability of the level 1 .. level 9
            # commands. I just need someone to help me with defining a mapping
            # between a percentage and a level
        else:
            raise ValueError("Unsupported packettype")


###############################################################################
# RFXtrxEvent class
###############################################################################

class RFXtrxEvent(object):
    """ Abstract superclass for all events """

    def __init__(self, device):
        """Constructor"""
        self.device = device


###############################################################################
# SensorEvent class
###############################################################################

class SensorEvent(RFXtrxEvent):
    """ Concrete class for sensor events """

    def __init__(self, pkt):
        """Constructor"""
        device = RFXtrxDevice(pkt)
        super(SensorEvent, self).__init__(device)

        self.values = {}
        if isinstance(pkt, lowlevel.Temp) \
                or isinstance(pkt, lowlevel.TempHumid) \
                or isinstance(pkt, lowlevel.TempHumidBaro):
            self.values['Temperature'] = pkt.temp
        if isinstance(pkt, lowlevel.Humid) \
                or isinstance(pkt, lowlevel.TempHumid) \
                or isinstance(pkt, lowlevel.TempHumidBaro):
            self.values['Humidity'] = pkt.humidity
            self.values['Humidity status'] = pkt.humidity_status_string
            self.values['Humidity status numeric'] = pkt.humidity_status
        if isinstance(pkt, lowlevel.Baro) \
                or isinstance(pkt, lowlevel.TempHumidBaro):
            self.values['Barometer'] = pkt.barometer
            self.values['Forecast'] = pkt.forecast_string
            self.values['Forecast numeric'] = pkt.forecast
        self.values['Battery numeric'] = pkt.battery
        self.values['Rssi numeric'] = pkt.rssi

    def __str__(self):
        return "{0} device=[{1}] values={2}".format(
            type(self), self.device, self.values)


###############################################################################
# ControlEvent class
###############################################################################

class ControlEvent(RFXtrxEvent):
    """ Concrete class for control events """

    def __init__(self, pkt):
        """Constructor"""
        if isinstance(pkt, lowlevel.Lighting1) \
                or isinstance(pkt, lowlevel.Lighting2) \
                or isinstance(pkt, lowlevel.Lighting3):
            device = LightingDevice(pkt)
        else:
            device = RFXtrxDevice(pkt)
        super(ControlEvent, self).__init__(device)

        self.values = {}
        if isinstance(pkt, lowlevel.Lighting1) \
                or isinstance(pkt, lowlevel.Lighting2) \
                or isinstance(pkt, lowlevel.Lighting3):
            self.values['Command'] = pkt.cmnd_string
        if isinstance(pkt, lowlevel.Lighting2) and pkt.cmnd in [2, 5]:
            self.values['Dim level'] = pkt.level * 100 / 15
        if isinstance(pkt, lowlevel.Lighting3):
            self.values['Battery numeric'] = pkt.battery
        self.values['Rssi numeric'] = pkt.rssi

    def __str__(self):
        return "{0} device=[{1}] values={2}".format(
            type(self), self.device, self.values)