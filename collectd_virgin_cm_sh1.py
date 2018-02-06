#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# collectd-python script to collect information from Virgin SuperHub v1
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
# CM URL notes:
#
# http://192.168.100.1/VmRouterStatus_info.asp
# http://192.168.100.1/VmRouterStatus_configuration.asp
# http://192.168.100.1/VmRouterStatus_upstream.asp
# http://192.168.100.1/VmRouterStatus_downstream.asp
# http://192.168.100.1/VmRouterStatus_usburst.asp
#
# This one is odd - it has headings, but not ths. Ignoring for now.
# http://192.168.100.1/VmRouterStatus_status.asp

import pprint
import sys

import bs4
import requests

__version__ = '0.0.1'
__author__ = 'noodles@earth.li'

URLBASE = 'http://192.168.100.1/'

status_pages = {
    'VmRouterStatus_info.asp': {
        'Information': {
            'Cable Modem':       'type',
            'Serial Number':     'serialno',
            'Boot Code Version': 'bootcodever',
            'Software Version':  'softwarever',
            'Hardware Version':  'hardwarever',
            'CA Key':            'cakey',
        },
    },
    'VmRouterStatus_configuration.asp': {
        'General Configuration': {
            'Network Access':         'access',
            'Maximum Number of CPEs': 'maxcpe',
            'Baseline Privacy':       'privacy',
            'DOCSIS Mode':            'docsis',
            'Config File':            'config',
        },
        'Primary Downstream Service Flow': {
            'SFID':                   'down_sfid',
            'Max Traffic Rate':       'down_maxrate',
            'Max Traffic Burst':      'down_maxburst',
            'Min Traffic Rate':       'down_minrate',
        },
        'Primary Upstream Service Flow': {
            'SFID':                   'up_sfid',
            'Max Traffic Rate':       'up_maxrate',
            'Max Traffic Burst':      'up_maxburst',
            'Min Traffic Rate':       'up_minrate',
            'Max Concatenated Burst': 'up_maxconcatburst',
            'Scheduling Type':        'up_scheduling',
        }
    },
    'VmRouterStatus_upstream.asp': {
        'Upstream': {
            'Channel Type':          'chantype',
            'Channel ID':            'chanid',
            'Frequency (Hz)':        'freq',
            'Ranging Status':        'ranging',
            'Modulation':            'modulation',
            'Symbol Rate (Sym/sec)': 'symrate',
            'Mini-Slot Size':        'slotsize',
            'Power Level (dBmV)':    'power',
            'T1 Timeouts':           't1timeouts',
            'T2 Timeouts':           't2timeouts',
            'T3 Timeouts':           't3timeouts',
            'T4 Timeouts':           't4timeouts',
        },
    },
    'VmRouterStatus_downstream.asp': {
        'Downstream': {
            'Frequency (Hz)':                           'freq',
            'Lock Status(QAM Lock/FEC Sync/MPEG Lock)': 'lock',
            'Channel ID':                               'chanid',
            'Modulation':                               'modulation',
            'Symbol Rate (Msym/sec)':                   'symrate',
            'Interleave Depth':                         'interleavel',
            'Power Level (dBmV)':                       'power',
            'RxMER (dB)':                               'rxmer',
        }
    },
    'VmRouterStatus_usburst.asp': {
        'Upstream Burst': {
            'Modulation Type':                          'modulation',
            'Differential Encoding':                    'diffenc',
            'Preamble Length':                          'preamblelen',
            'Preamble Value Offset':                    'preambleoff',
            'FEC Error Correction (T)':                 'fec',
            'FEC Codeword Information Bytes (K)':       'fecbytes',
            'Maximum Burst Size':                       'maxburst',
            'Guard Time Size':                          'guardtime',
            'Last Codeword Length':                     'lastcwlen',
            'Scrambler On/Off':                         'scrambler',
        },
    },
}

def parse_page(page):
    if not page in status_pages:
        raise Exception('Unknown status page')

    table_map = status_pages[page]
    url = requests.get(URLBASE + page)
    soup = bs4.BeautifulSoup(url.text)
    info = {}

    for table in soup.find_all('table'):
        columns = None
        caption = table.find('caption')
        if caption.contents[0] not in table_map:
            raise Exception('Unexpected table in page ' + caption.contents[0])

        field_map = table_map[caption.contents[0]]

        columnheader = table.find('thead')
        if columnheader:
            columns = []
            for column in columnheader.find_all('th'):
                if column.contents[0] != u'\xA0':
                    columns.append(column.contents[0])
                    info[column.contents[0]] = {}

        for row in table.find_all('tr'):
            title = row.find('td', { "class": "title" })
            if not title:
                continue
            if title.contents[0] not in field_map:
                raise Exception('Unexpected field in table ' +
                                title.contents[0])

            field = field_map[title.contents[0]]
            if columns:
                colidx = 0
                for data in title.find_next_siblings('th'):
                    if data.contents:
                        value = data.contents[0].strip()
                        info[columns[colidx]][field] = value
                        colidx += 1
            else:
                data = title.find_next_sibling('td')
                if data.contents:
                    value = data.contents[0].strip()
                    info[field] = value

    return info

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
        info = parse_page('VmRouterStatus_configuration.asp')

        down = info['down_maxrate']
        down = down.split(' ')[0]
        up = info['up_maxrate']
        up = up.split(' ')[0]

        self.dispatch_value('cm1', 'bitrate', 'max-down', down)
        self.dispatch_value('cm1', 'bitrate', 'max-up', up)

        info = parse_page('VmRouterStatus_downstream.asp')
        for channel in info:
            if info[channel]['power'] == "N/A":
                continue
            power = info[channel]['power']
            power = power.split(' ')[0]

            self.dispatch_value('cm1', 'gauge', channel + "-power", power)

        info = parse_page('VmRouterStatus_upstream.asp')
        for channel in info:
            if info[channel]['power'] == "N/A":
                continue
            power = info[channel]['power']
            power = power.split(' ')[0]

            self.dispatch_value('cm1', 'gauge', channel + "-power", power)

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
    info = parse_page('VmRouterStatus_configuration.asp')

    down = info['down_maxrate']
    down = down.split(' ')[0]
    up = info['up_maxrate']
    up = up.split(' ')[0]

    print "cm1.down:%s" % (down)
    print "cm1.up:%s" % (up)

    sys.exit(0)
else:
    import collectd

    cmmon = CMMon()

    collectd.register_config(cmmon.configure_callback)
