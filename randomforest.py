import csv
import time
import sys

from scapy.all import sendp, send, get_if_list, get_if_hwaddr, hexdump
from scapy.all import Packet
from scapy.all import Ether, IP, UDP, TCP
from randomforest_header import RandomForestPacket

def main():
    with open('titanic_testing.csv') as csvfile:
        reader = csv.reader(csvfile, quotechar='"')
        next(reader, None) # skip header
        passenger_list = list(reader)

    # def get_if():
    #     ifs=get_if_list()
    #     iface=None # "h1-eth0"
    #     for i in ifs:
    #         if "eth0" in i:
    #             iface=i
    #             break
    #     if not iface:
    #         print("Cannot find eth0 interface")
    #         exit(1)
    #     return iface

    # iface = get_if()

    # print(passenger_list)
    # 0! PassengerId, 1! Survived, 2! Pclass, 3 Name, 4! Sex, 5! Age, 6 SibSp, 7 Parch, 8 Ticket, 9! Fare, 10 Cabin, 11 Embarked

    for passenger in passenger_list:
        if (passenger[0] == '' or 
            passenger[1] == '' or 
            passenger[2] == '' or 
            passenger[4] == '' or 
            passenger[5] == '' or 
            passenger[9] == ''):
            continue
        else:
            # print(passenger)
            pkt = Ether(src='ee:ee:ee:ee:ee:ee', dst='ff:ff:ff:ff:ff:ff')

            pId = int(passenger[0])
            age = int(float(passenger[5]))
            sex = 1 if passenger[4] == 'male' else 0
            pClass = int(passenger[2])
            fare = int(float(passenger[9]))
            survived = int(passenger[1])

            pkt = pkt / RandomForestPacket(id = pId, age = age, sex = sex, p_class = pClass, fare = fare, survived = survived, switch_survived = 0, counter = 0, depth = 0)
            # pkt = pkt / ' '
            
            sys.stdout.flush()
            print("Sending packet:")
            pkt.show2()
            # time.sleep(1)
            sendp(pkt)

if __name__ == '__main__':
    main()