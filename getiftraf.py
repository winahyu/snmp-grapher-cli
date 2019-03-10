#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import time
import pprint
import argparse
from easysnmp import Session
from si_prefix import si_format
from terminalplot import plot
from terminalplot import get_terminal_size
from collections import deque
import datetime

class colors:
    RED = '\033[0;91m'
    GREEN = '\033[0;92m'
    BLUE = '\033[0;94m'
    CYAN = '\033[0;96m'
    YELLOW = '\033[0;93m'
    URed = "\033[4;91m"         # Red
    UGreen = "\033[4;92m"       # Green
    UYellow = "\033[4;93m"      # Yellow
    UBlue = "\033[4;34m"        # Blue
    UPurple = "\033[4;35m"      # Purple
    UCyan = "\033[4;96m"        # Cyan

def get_args():
    """
   Supports the command-line arguments listed below.
   """
    parser = argparse.ArgumentParser(
        description='Process args for retrieving device interface via SNMP')
    parser.add_argument('-H', '--host', required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-p', '--port', type=int, default=161, action='store',
                        help='Port to connect on')
    parser.add_argument('-c', '--community', required=True, action='store',
                        help='SNMP Community')
    args = parser.parse_args()
    return args

args = get_args()

hostname =  args.host
community = args.community


def print_xy(y, x, color, text):
     sys.stdout.write("\x1b7\x1b[%d;%df%s%s\x1b8" % (x, y, color, text))
     sys.stdout.flush()

def selection_menu():
    print colors.YELLOW + '\nSelect Interface to monitor (q to quit): ',
    return raw_input()


session = Session(hostname=hostname, community=community, version=2)


while True:
    system_items = session.walk('1.3.6.1.2.1.31.1.1.1.1')
    count_item = 0
    for item in system_items:
        int_index = item.oid
        int_index = int_index.rsplit(".",2)

        color_line = colors.CYAN if (count_item % 2 == 0) else colors.UCyan
        print  color_line + "Interface index : " + str(int_index[2]),

        color_line = colors.GREEN if (count_item % 2 == 0) else colors.UGreen
        print color_line + '\t\tIF System Name : {value}'.format(value=item.value),
        int_desc = session.get(("1.3.6.1.2.1.31.1.1.1.18",int_index[2]))
        if len(int_desc.value) == 0:
            int_desc = session.get(("1.3.6.1.2.1.2.2.1.2",int_index[2]))

        color_line = colors.YELLOW if (count_item % 2 == 0) else colors.UYellow
        print color_line + "\t\t\tInterface Desc : " + int_desc.value
        count_item += 1

    choice = selection_menu()
    if choice == "q":
        sys.exit(0);
    else:
        if_id = choice
        break

st_inoctets =  session.get(('1.3.6.1.2.1.2.2.1.10',if_id))
st_outoctets = session.get(('1.3.6.1.2.1.2.2.1.16',if_id))
if_name = session.get(('1.3.6.1.2.1.2.2.1.2',if_id))

start_time = time.time()
exec_time = datetime.datetime.now()

inpos = deque([])
outpos = deque([])


while True:

    terminal_size = get_terminal_size()
    system_items = session.walk('1.3.6.1.2.1.2.2.1.2')

    time.sleep(5)
    print(chr(27) + "[2J")

    inoctets =  session.get(('1.3.6.1.2.1.2.2.1.10',if_id))
    outoctets = session.get(('1.3.6.1.2.1.2.2.1.16',if_id))

    endtime = time.time()
    difftime = endtime - start_time

    inbytes = int(round((int(inoctets.value) - int(st_inoctets.value))/difftime))
    outbytes = int(round((int(outoctets.value) - int(st_outoctets.value))/difftime))

    while len(inpos) > terminal_size[1]:
        inpos.pop()
        outpos.pop()


    inpos.appendleft(inbytes*8)
    outpos.appendleft(outbytes*8)

    reverse_graph = 0
    max_y = max(inpos)
    if max_y < max(outpos):
        max_y = max(outpos)
        reverse_graph = 1


    y_size = terminal_size[0] - 4

    y_factor = (y_size * 1.)/ (max_y+1)


    #### PLOT GRAPH
    x_count = 1
    y_out = []

    for outpos_y in outpos:
        pos_y = int(round(outpos_y * y_factor))
        y_out.append(pos_y)
        x_count += 1

    y_in = []

    for inpos_y in inpos:
        pos_y = int(round(inpos_y * y_factor))
        y_in.append(pos_y)

    if reverse_graph == 1:
        for x in range(1,x_count):
            print_xy(x,y_size+1,colors.YELLOW,"══>>")

            for y in range (y_size - y_out[x-1]+5, y_size ):
                print_xy(x,y,colors.GREEN,"▒")
            for y in range (y_size - y_in[x-1]+5, y_size ):
                print_xy(x,y,colors.RED,"▒")
    else:
        for x in range(1,x_count):
            print_xy(x,y_size+1,colors.YELLOW,"══>>")
            for y in range (y_size - y_in[x-1]+5, y_size ):
                print_xy(x,y,colors.RED,"▒")
            for y in range (y_size - y_out[x-1]+5, y_size ):
                print_xy(x,y,colors.GREEN,"▒")

    print_xy(1,y_size+1,colors.YELLOW,"Interface : " + if_name.value + " >>")


    last_time = datetime.datetime.now()

    footer_1 = "Input traffic/sec: %sbits (%sbytes), Peak Value: %sbits" % (si_format(inbytes*8,precision=3),si_format(inbytes,precision=3),si_format(max(inpos),precision=3))
    footer_2 = "Output traffic/sec: %sbits (%sbytes), Peak Value: %sbits" % (si_format(outbytes*8,precision=3),si_format(outbytes,precision=3),si_format(max(outpos),precision=3))

    run_time = endtime - time.mktime(exec_time.timetuple())

    footer_3 = "Current Time : %s, Ruuning Time : %s, Collection time: %s seconds " % (last_time.strftime("%Y-%m-%d %H:%M:%S"),datetime.datetime.utcfromtimestamp(run_time).strftime("%H:%M:%S"),int(round(difftime)))

    print_xy(1, y_size+2,colors.RED,footer_1)
    print_xy(1, y_size+3,colors.GREEN,footer_2)
    print_xy(1, y_size+4,colors.CYAN,footer_3)

    start_time = endtime

    st_inoctets = inoctets
    st_outoctets = outoctets


