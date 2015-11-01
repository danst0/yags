#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YAGS (Yet another GCode Sender)

Usage:
  yags.py send <filename> [--port=<serial_port>]
  yags.py list_ports
  yags.py (-h | --help)
  yags.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt
import sys
import glob
import serial

# Serial code from http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
def serial_ports():
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def detect_relevant_port(list_of_ports):
  return '/dev/xxx'

def detect_baud_rate(serial_port):
  return 19200

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Yags (Yet another GCode Sender) 0.1')
    print(arguments)
    list_of_ports = serial_ports()
    print(list_of_ports)
    serial_port = detect_relevant_port(list_of_ports)
    baudrate = detect_baud_rate(serial_port)
    ser = serial.Serial(port=serial_port, baudrate=baudrate, timeout=30)
    for line in sys.stdin.readlines():
      ser.write(line)
      print line.strip('\n')
      while True:
        response = ser.readline()
        print response
        if response.strip() in ['ok','start']:
            break
    ser.close()