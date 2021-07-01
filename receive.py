#!/usr/bin/env python
import sys
import struct
import os

from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr
from scapy.all import Packet, IPOption
from scapy.all import ShortField, IntField, LongField, BitField, FieldListField, FieldLenField
from scapy.all import IP, TCP, UDP, Raw
from scapy.layers.inet import _IPOption_HDR
from randomforest_header import RandomForestPacket

# def get_if():
#     ifs=get_if_list()
#     iface=None
#     for i in get_if_list():
#         if "eth0" in i:
#             iface=i
#             break
#     if not iface:
#         print("Cannot find eth0 interface")
#         exit(1)
#     return iface

results = []

def handle_pkt(pkt):
    if RandomForestPacket in pkt:
        randomForestPacket=pkt[RandomForestPacket]
        print("Received packet with Id: %s" % randomForestPacket.id)
        print("Number of switches reached: %s" % randomForestPacket.counter)
        print("Maximum reached depth: %s" % randomForestPacket.depth)
        print("Predicted survival: %s, actual survival: %s" %(randomForestPacket.switch_survived, randomForestPacket.survived))
        results.append((randomForestPacket.switch_survived, randomForestPacket.survived))
        success = float(len([y for x,y in results if x == y]))
        allPackage = float(len(results))
        print("The total accuracy up to this point: %s" %((success/allPackage)*100))
        print("")
        # pkt.show2()
        sys.stdout.flush()


def main():
    # ifaces = filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/'))
    iface = 'eth0' #ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()