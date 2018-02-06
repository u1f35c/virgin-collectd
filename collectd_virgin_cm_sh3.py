#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# collectd-python script to collect information from Virgin SuperHub v3
# Copyright Ⓒ 2017 Jonathan McDowell <noodles@earth.li>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import pprint
import sys

import requests

__version__ = '0.0.1'
__author__ = 'noodles@earth.li'

URLBASE = 'http://192.168.100.1/'

keymap = {
    'downstream': {
        'snmpbase': '1.3.6.1.2.1.10.127.1.1.1',
        'keys': {
            '1.1': 'chanid',
            '1.2': 'freq',
            '1.3': 'width',
            '1.4': 'modulation',
            '1.5': 'interleave',
            '1.6': 'power',
            '1.7': 'annex',
            '1.8': 'storage',
        },
    },
    'upstream': {
        'snmpbase': '1.3.6.1.2.1.10.127.1.1.2',
        'keys': {
            '1.1':  'chanid',
            '1.2':  'freq',
            '1.3':  'width',
            '1.4':  'modulation',
            '1.5':  'slotsize',
            '1.6':  'timingofs',
            '1.7':  'backoffstart',
            '1.8':  'backoffend',
            '1.9':  'txbackoffstart',
            '1.10': 'txbackoffend',
            '1.11': 'scdmaactivecodes',
            '1.12': 'scdmacodesperslot',
            '1.13': 'scdmaframesize',
            '1.14': 'scdmahoppingspeed',
            '1.15': 'type',
            '1.16': 'clonefrom',
            '1.17': 'update',
            '1.18': 'status',
            '1.19': 'preeqenable',
        },
    },
    'upstreamext': {
        'snmpbase': '1.3.6.1.4.1.4115.1.3.4.1.9.2',
        'keys': {
            '1.1':  'chanid',
            '1.2':  'symrate',
            '1.3':  'modulation',
        },
    },
    'upstreamstatus': {
        'snmpbase': '1.3.6.1.4.1.4491.2.1.20.1.2',
        'keys': {
            '1.1':  'power',
            '1.2':  't3timeouts',
            '1.3':  't4timeouts',
            '1.4':  'rangingaborteds',
            '1.5':  'modulation',
            '1.6':  'eqdata',
            '1.7':  't3exceededs',
            '1.8':  'ismuted',
            '1.9':  'ranging',
        },
    },
    'signalqualityext': {
        'snmpbase': '1.3.6.1.4.1.4491.2.1.20.1.24',
        'keys': {
            '1.1':  'rxmer',
            '1.2':  'rxmersamples',
        },
    },
    'qos': {
        'snmpbase': '1.3.6.1.4.1.4491.2.1.21.1.2.1.6',
        'keys': {
            '2.1':  'maxrate',
            '2.2':  None,
            '2.3':  None,
        },
    },
    'qosflows': {
        'snmpbase': '1.3.6.1.4.1.4491.2.1.21.1.3.1',
        'keys': {
            '6.2':  'sfsid',
            '7.2':  'direction',
            '8.2':  'primary',
            '9.2':  'flowparam',
            '10.2': 'chansetid',
            '11.2': 'flowattrsuccess',
            '12.2': 'sfdsid',
            '13.2': None,
            '14.2': None,
            '15.2': None,
            '16.2': None,
            '17.2': None,
        },
    },
}


def snmpget(page, flatten=None):
    r = requests.get(URLBASE + 'walk?oids=' + keymap[page]['snmpbase'])
    jdata = r.json()
    data = {}
    for key in jdata:
        if jdata[key] == 'Finish':
            continue
        keyext = key[len(keymap[page]['snmpbase']) + 1:key.rfind('.')]
        index = key[key.rfind('.') + 1:]
        if index not in data:
            data[index] = {}
        if keyext not in keymap[page]['keys']:
            print("Unknown:", keymap[page]['snmpbase'], keyext, index, ':' +
                  jdata[key] + ':')
        elif keymap[page]['keys'] is None:
            1  # Ignore
        else:
            data[index][keymap[page]['keys'][keyext]] = jdata[key]

    if flatten is None:
        return data

    newdata = []
    for channel in sorted(data.values(), key=lambda x: int(x[flatten])):
        newdata.append(channel)

    return newdata


def getmaxspeeds():
    qos = snmpget('qos')
    qosflows = snmpget('qosflows')

    down = up = 0

    for (key, entry) in qosflows.items():
        if int(entry['primary']) == 1:
            if int(entry['direction']) == 1:
                down = int(qos[key]['maxrate'])
            elif int(entry['direction']) == 2:
                up = int(qos[key]['maxrate'])

    return (up, down)


class CMMon(object):
    def __init__(self):
        self.plugin_name = 'collectd-virgin-cm'
        self.interval = 60
        self.verbose_logging = False

    def log(self, msg):
        if self.verbose_logging:
            collectd.info('%s plugin [verbose]: %s' % (self.plugin_name, msg))

    def dispatch_value(self, plugin_instance, val_type, type_instance, value):
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = val_type
        if len(type_instance):
            val.type_instance = type_instance
        val.values = [value, ]
        val.meta = {'0': True}
        val.dispatch()

    def dispatch_values(self, plugin_instance, val_type, type_instance, value1,
                        value2):
        val = collectd.Values()
        val.plugin = self.plugin_name
        val.plugin_instance = plugin_instance
        val.type = val_type
        if len(type_instance):
            val.type_instance = type_instance
        val.values = [value1, value2]
        val.meta = {'0': True}
        val.dispatch()

    def read_callback(self):
        (up, down) = getmaxspeeds()

        self.dispatch_value('cm1', 'bitrate', 'max-down', down)
        self.dispatch_value('cm1', 'bitrate', 'max-up', up)

        downstream = snmpget('downstream', flatten='chanid')

        for (i, channel) in enumerate(downstream):
            power = int(channel['power']) / float(10)

            self.dispatch_value('cm1', 'gauge', "DS-" + str(i + 1) + "-power",
                                power)

        upstream = snmpget('upstream')
        # upstreamext = snmpget('upstreamext', flatten='chanid')
        upstreamstatus = snmpget('upstreamstatus')

        i = 1
        for channel in sorted(upstream.items(),
                              key=lambda x: int(x[1]['chanid'])):
            power = int(upstreamstatus[channel[0]]['power']) / float(10)

            self.dispatch_value('cm1', 'gauge', "US-" + str(i) + "-power",
                                power)
            i += 1

    def configure_callback(self, conf):
        for node in conf.children:
            val = str(node.values[0])

            if node.key == 'Interval':
                self.interval = float(val)
            elif node.key == 'Verbose':
                self.verbose_logging = val in ['True', 'true']
            else:
                collectd.warning('%s plugin: Unknown config key: %s.' % (
                                     self.plugin_name, node.key))

        collectd.register_read(self.read_callback, self.interval)


if __name__ == '__main__':
    (up, down) = getmaxspeeds()

    print "cm1.down:%s" % (down)
    print "cm1.up:%s" % (up)

    sys.exit(0)
else:
    import collectd

    cmmon = CMMon()

    collectd.register_config(cmmon.configure_callback)
