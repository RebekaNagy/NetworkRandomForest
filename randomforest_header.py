import argparse
import sys
import socket
import random
import struct
import re

from scapy.all import sendp, send, srp1
from scapy.all import Packet, hexdump
from scapy.all import Ether, StrFixedLenField, XByteField, IntField
from scapy.all import bind_layers

class RandomForestPacket(Packet):
    name = "RandomForestPacket"
    fields_desc = [ IntField("id", 0),
                    IntField("age", 0),
                    IntField("sex", 0),
                    IntField("p_class", 0),
                    IntField("fare", 0),
                    IntField("survived", 0),
                    IntField("switch_survived", 0),
                    IntField("counter", 0),
                    IntField("depth", 0) ]

bind_layers(Ether, RandomForestPacket, type=0x1234)