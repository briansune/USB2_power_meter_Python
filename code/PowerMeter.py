import sys
import glob
import serial
import time
import re


class PowerMeter:

    def __init__(self):
        self.port = 'COM15'
        self.sys_ports = []
        self.baud = 921600
        self.serial_holder = serial.Serial()

    def port2list(self):
        if sys.platform.startswith('win'):
            self.sys_ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            self.sys_ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            self.sys_ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in self.sys_ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def connect2meter(self):
        self.serial_holder = serial.Serial(self.port, self.baud, timeout=0.5)
        port_status = self.serial_holder.isOpen()
        if port_status:
            self.serial_holder.close()
        self.serial_holder.open()

    def start2meter(self):
        self.serial_holder.write(b'Read\x0D\x0A')

    def fastrate4meter(self):
        self.serial_holder.write(b'S2\x0D\x0A')

    def medrate4meter(self):
        self.serial_holder.write(b'S1\x0D\x0A')

    def slowrate4meter(self):
        self.serial_holder.write(b'S0\x0D\x0A')

    def read4power(self):
        return self.serial_holder.read_all()

    def close(self):
        self.serial_holder.close()


def main():
    print 'test power meter'
    pwrm_hdr = PowerMeter()
    print pwrm_hdr.port2list()
    pwrm_hdr.connect2meter()
    pwrm_hdr.start2meter()
    l_pwr_offset = []
    while True:
        res_pwr = pwrm_hdr.read4power()
        o_match_raw = re.search('R([0-9]{4}[+-][0-9]{2}[.][0-9]){9}[A]', res_pwr)
        if o_match_raw:
            l_pwr_offset = re.findall('([0-9]{4})([+-][0-9]{2}[.][0-9])', o_match_raw.group())
            print l_pwr_offset
            break

    pwrm_hdr.fastrate4meter()
    pwrm_hdr.serial_holder.reset_input_buffer()
    pwrm_hdr.serial_holder.reset_output_buffer()
    pwrm_hdr.serial_holder.flush()

    while True:
        res_pwr = pwrm_hdr.read4power()
        time.sleep(2)
        l_raw_data = re.findall('a([-+][0-9]{3})[0-9]{5}[umW][A]', res_pwr)
        if l_raw_data:
            l_float_data = [float(s_raw) / 10 for s_raw in l_raw_data]
            print sum(l_float_data) / len(l_float_data), len(l_float_data)


if __name__ == '__main__':
    main()
