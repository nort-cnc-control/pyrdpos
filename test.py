import rdpos
import serial
import sys
import time

port = sys.argv[1]
baudrate = 115200
ser = serial.Serial(port, baudrate, bytesize=8, parity='N', stopbits=1)
t = rdpos.RDPoSConnection(ser)
t.connect(1,1)
hello = t.read()
print(hello)
#time.sleep(15)
t.close()
t.finish()
