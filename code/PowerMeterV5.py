import sys
import glob
import serial
import time
import re


class PowerMeter:

    def __init__(self):
        self.port = 'COM17'
        self.sys_ports = []
        self.baud = 921600
        self.average = 10
        self.l_pwr_offset = []
        self.l_pwr_trace = []
        self.serial_holder = serial.Serial()

        # 1 - 100us 500k sample / second
        # 2 - 2ms 250k sample / second
        # 3 - 3ms 125k sample / second
        # 4 - 5ms 62.5k sample / second
        # 5 - 10ms 31.25k sample / second
        # 6 - 20ms 15.625k sample / second
        # 7 - 40ms 7.81k sample / second
        # 8 - 60ms 3.91k sample / second
        # 9 - 100ms 3.91k sample / second
        # 10 - 150ms 1.95k sample / second
        # 11 - 200ms 1.95k sample / second
        # 12 - 400ms 0.98k sample / second
        # 13 - 600ms 0.49k sample / second
        # 14 - 1s 0.24k sample / second
        # 15 - 1.5s 0.24k sample / second
        # 16 - 2s 0.12k sample / second
        # 17 - 3s 0.12k sample / second
        # 18 - 5s 0.06k sample / second
        self.sample_wait = [0.002, 0.004, 0.006, 0.01, 0.02, 0.03, 0.04, 0.08, 0.12, 0.2,
                            0.4, 0.8, 1.2, 2, 3, 4, 6, 10]
        self.sample_select = 1

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
        self.serial_holder = serial.Serial(self.port, self.baud, timeout=5)
        port_status = self.serial_holder.isOpen()
        if port_status:
            self.serial_holder.close()
        self.serial_holder.open()

    def start2meter(self):
        self.offset4meter()
        while True:
            res_pwr = self.serial_holder.read_all()
            o_match_raw = re.search('R([0-9]{4}[+-][0-9]{2}[.][0-9])[A]', res_pwr)
            if o_match_raw:
                l_pwr_offset = re.findall('([0-9]{4})([+-][0-9]{2}[.][0-9])', o_match_raw.group())
                self.l_pwr_offset = [[float(s_raw[0]), float(s_raw[1])] for s_raw in l_pwr_offset]
                return

    def samplerate4meter(self):
        print b'K{:02d}\x0D\x0A'.format(self.sample_select)
        self.serial_holder.write(b'K{:02d}\x0D\x0A'.format(self.sample_select))

    def offset4meter(self):
        self.serial_holder.write(b'Read\x0D\x0A')

    def read4power(self):
        self.l_pwr_trace = []
        self.samplerate4meter()
        while True:
            # time.sleep(self.sample_wait[self.sample_select - 1] * 30)
            res_pwr = self.serial_holder.read_until(size=14000)
            o_match_raw = re.search('a([-+][0-9]{3}[0-9]{5}[umW])*A', res_pwr)
            if o_match_raw:
                l_pwr_trace = re.findall('([-+][0-9]{3})[0-9]{5}[umW]', o_match_raw.group(0))
                self.l_pwr_trace = [float(s_raw) / 10.0 for s_raw in l_pwr_trace]
                return

    def close(self):
        self.serial_holder.close()


def main():
    average = 1000

    print 'test power meter'
    pwrm_hdr = PowerMeter()
    pwrm_hdr.average = average

    print pwrm_hdr.port2list()
    pwrm_hdr.connect2meter()
    pwrm_hdr.start2meter()
    print pwrm_hdr.l_pwr_offset

    time.sleep(1)
    for i in range(1, 18):
        pwrm_hdr.sample_select = i
        pwrm_hdr.read4power()
        print len(pwrm_hdr.l_pwr_trace)


if __name__ == '__main__':
    main()
