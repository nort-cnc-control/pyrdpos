#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import multiprocessing
import rdp
import serial_datagram
import timeout_decorator
import time
import random

class RDPoSConnection(object):
    def run_read_serial(self, evq):
        data = bytes()
        while not self.__finish.is_set():
            try:
                b = self.ser_port.read(1)
            except Exception as e:
                continue

            #if random.random() < 0.02:
            #    continue

            print("%02X" % b[0], end=" ")
            data += b
            if b != serial_datagram.END:
                continue
            print()
            print("RCVD DGRAM, %i" % len(data))
            try:
                dgram = serial_datagram.decode(data)
                evq.put(("dgram_recv", dgram))
            except:
                print("data loss")
                pass
            data = bytes()

    def __rdp_connected(self, conn):
        print("CONNECTED")
        self.__connected.set()
        self.__closed.clear()

    def __rdp_closed(self, conn):
        print("CLOSED")
        self.__connected.clear()
        self.__closed.set()

    def __dgram_send(self, conn, data):
        enc = serial_datagram.encode(data)
        print("SEND", end=" ")
        for b in enc:
            print("%02X" % b, end=" ")
        print()
        self.ser_port.write(enc)

    def __data_received(self, conn, data):
        self.__rcvd.put(data)

    def __data_transmitted(self, conn):
        self.__transmitted.set()

    def run_cycle(self, evq):
        rdpc = rdp.RDP()
        
        rdpc.set_dgram_send_cb(self.__dgram_send)
        rdpc.set_data_received_cb(self.__data_received)
        rdpc.set_data_transmitted_cb(self.__data_transmitted)
        rdpc.set_connected_cb(self.__rdp_connected)
        rdpc.set_closed_cb(self.__rdp_closed)

        while not self.__finish.is_set():
            try:
                msg = evq.get(timeout=1)
            except:
                continue
            mtype = msg[0]
            data = msg[1]
            if mtype == "connect":
                sport = data[0]
                dport = data[1]
                res = rdpc.connect(sport, dport)
            elif mtype == "close":
                res = rdpc.close()
            elif mtype == "send":
                res = rdpc.send(data)
            elif mtype == "dgram_recv":
                res = rdpc.dgram_receive(data)
            elif mtype == "reset":
                rdpc.reset()
            if not res:
                print("Data error")

    def __init__(self, ser_port):
        self.evq = multiprocessing.Queue()
        self.ser_port = ser_port

        self.__transmitted = multiprocessing.Event()
        self.__connected = multiprocessing.Event()
        self.__closed = multiprocessing.Event()
        self.__rcvd = multiprocessing.Queue()

        self.__finish = multiprocessing.Event()

        self.__listener = multiprocessing.Process(target=self.run_read_serial, args=(self.evq,))
        self.__cycle = multiprocessing.Process(target=self.run_cycle, args=(self.evq,))
        self.__listener.start()
        self.__cycle.start()

    def __dofinish(self):
        self.__finish.set()
        self.__cycle.join()
        self.__listener.join()

    def finish(self):
        self.__dofinish()

    def reset(self):
        self.evq.put(("reset", None))

    def connect(self, sport, dport):
        self.evq.put(("connect", (sport, dport)))
        self.__connected.wait()
        return True

    def send(self, data):
        if not self.__connected.is_set():
            return False
        self.evq.put(("send", data))
        self.__transmitted.wait()
        self.__transmitted.clear()
        return True

    def read(self):
        return self.__rcvd.get()

    def close(self):
        self.evq.put(("close", None))
        self.__closed.wait()
        return True
