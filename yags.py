#!/usr/local/bin/python3

from tkinter import *
from subprocess import call
import threading
import queue
import time, random
import serial

SISPMCTL = "/usr/local/bin/sispmctl"
UGS = "/Users/danieldumke/cnc/ugs/start.sh"

class GRBLSerial(Serial):
    def __init__(self, *args, **kwargs):
        port_list = self.list_serial_ports()
        print(port_list)
        my_port = self.detect_relevant_port(port_list)
        my_baud = self.detect_baud_rate(my_port)
        if not 'port' in kwargs:
            kwargs['port'] = my_port
        if not 'baudrate' in kwargs:
            kwargs['baudrate'] = my_baud
        super(ExtendedSerial, self).__init__(*args, **kwargs)

    # Serial code from http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
    def list_serial_ports():
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
    '''Connect to all serial ports and look for GRBL string'''
      return '/dev/cu.usbmodem441'

    def detect_baud_rate(serial_port):
      return 115200


class SerialController(threading.Thread):

    def __init__(self, command_queue, to_grbl_queue, from_grbl_queue):
        self.command_queue = command_queue
        self.to_grbl_queue = to_grbl_queue
        self.from_grbl_queue = from_grbl_queue
        threading.Thread.__init__(self)
        self.ser = serial.GRBLSerial()
        
        #ser.bytesize = serial.EIGHTBITS #number of bits per bytes
        #ser.parity = serial.PARITY_NONE #set parity check: no parity
        #ser.stopbits = serial.STOPBITS_ONE #number of stop bits
        #ser.timeout = 1
        #ser.writeTimeout = 2
        if not self.ser.isOpen():
            self.ser.open()


    def run(self):
        while 1:
            try:
                command = self.command_queue.get(block=False)
            except:
                command = ''
            if command != '':
                print('Serial command', command)
            if command == None:
                print('Stopping Serial Controller')
                self.ser.close()
                break # reached end of queue
            elif command == 'connect':
                self.to_grbl_queue.queue.clear()
                if not self.ser.isOpen():
                    self.ser.open()

            elif command == 'disconnect':
                if self.ser.isOpen():
                    self.ser.close()
            try:
                ser_data = self.to_grbl_queue.get(block=False)
            except:
                ser_data = ''

            # pretend we're doing something that takes 10-100 ms
            time.sleep(1)
            if self.ser.isOpen():
                if ser_data != '':
                    print("Sending to grbl:", ser_data)
                    self.ser.write(bytes(ser_data, 'UTF-8'))

                try:
                    read_ser_data = self.ser.read(9999)
                except:
                    pass
                else:
                    if ser_data != '':
                        print('Received from grbl', read_ser_data)
                        self.from_grbl_queue.put(read_ser_data)


class PMSController(threading.Thread):

    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            item = self.__queue.get()
            if item is None:
                print('Stopping PMS Controller')
                break # reached end of queue

            # pretend we're doing something that takes 10-100 ms
            #time.sleep(random.randint(10, 100) / 1000.0)
            print("exec sispmctl with:", item, "started")
            call([SISPMCTL, item[0], str(item[1])])



class App(Tk):
    def button_command(self, i):
        #print('i', i)
        #print('Outlet', self.outlet[i])
        #print('State', self.variable[i].get())
        if self.variable[i].get() == 1:
            param = "-o"
        else:
            param = "-f"
        self.pms_queue.put([param, self.outlet[i]])
        #call([SISPMCTL, param, str(self.outlet[i])])


    def request_serial_status(self):
        if not self.exiting:
            threading.Timer(5.0, self.request_serial_status).start()
            self.serial_to_grbl_queue.put('?')

    def update_gui_serial_status(self):
        if not self.exiting:
            threading.Timer(5.0, self.update_gui_serial_status).start()
            current_text = self.serial_from_grbl_queue.get()
            print(current_text)
            self.text_field_serial_output.insert('1.0', current_text)


    def build_main_window(self):
        menubar = Menu(self)
        #self.config(menu=menubar)

        # Create a menu button labeled "File" that brings up a menu
        filemenu = Menu(menubar)
        menubar.add_cascade(label='File', menu=filemenu)

        # Create entries in the "File" menu
        # simulated command functions that we want to invoke from our menus
        filemenu.add_command(label='Open', command=print)
        filemenu.add_separator(  )
        filemenu.add_command(label='Quit', command=sys.exit)

    def cb_autoconnect(self):
        if self.autoconnect_serial.get():
            self.serial_command_queue.put('connect')
        else:
            self.serial_command_queue.put('disconnect')


    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        #self.build_main_window()
        self.grid()
        self.exiting = False

        self.autoconnect_serial = IntVar()
        self.autoconnect_serial.set(1)

        self.variable = {'LEDs': IntVar(), 'Controller': IntVar(), 'Spindle': IntVar()}
        for key, val in self.variable.items():
            val.set(1)
        text = ["LEDs", "Controller", "Spindle"]
        self.outlet = {'LEDs': 4, 'Controller': 3, 'Spindle': 2}

        self.pms_queue = queue.Queue(0)
        PMSController(self.pms_queue).start()

        self.serial_command_queue = queue.Queue(0)
        self.serial_from_grbl_queue = queue.Queue(0)
        self.serial_to_grbl_queue = queue.Queue(0)
        SerialController(self.serial_command_queue, self.serial_to_grbl_queue, self.serial_from_grbl_queue).start()
        cur_row = 0
        Label(text='LEDs', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.variable['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.variable['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Controller', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.variable['Controller'], command=lambda: self.button_command('Controller'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.variable['Controller'], command=lambda: self.button_command('Controller'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Spindle', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.variable['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.variable['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=2).grid(row=cur_row, column=2)


        cur_row +=1
        Label(text='Work Position', width=15).grid(row=cur_row, column=0, sticky="E")
        Label(text='X', width=15).grid(row=cur_row, column=1, sticky="E")
        self.wp_x = Label(text='0.0', width=15)
        self.wp_x.grid(row=cur_row, column=2)
        Label(text='Machine Position', width=15).grid(row=cur_row, column=3, sticky="E")
        Label(text='X', width=15).grid(row=cur_row, column=4, sticky="E")
        self.machine_x = Label(text='0.0', width=15)
        self.machine_x.grid(row=cur_row, column=5)

        cur_row += 1
        Label(text='Y', width=15).grid(row=cur_row, column=1, sticky="E")
        self.wp_y = Label(text='0.0', width=15)
        self.wp_y.grid(row=cur_row, column=2)
        Label(text='Y', width=15).grid(row=cur_row, column=4, sticky="E")
        self.machine_y= Label(text='0.0', width=15)
        self.machine_y.grid(row=cur_row, column=5)

        cur_row += 1
        Label(text='Z', width=15).grid(row=cur_row, column=1, sticky="E")
        self.wp_z = Label(text='0.0', width=15)
        self.wp_z.grid(row=cur_row, column=2)
        Label(text='Z', width=15).grid(row=cur_row, column=4, sticky="E")
        self.machine_z = Label(text='0.0', width=15)
        self.machine_z.grid(row=cur_row, column=5)


        cur_row += 1
        Button(self, text="UGS", command=self.call_ugs).grid(row=cur_row, column=0)

        Button(self, text="Exit", fg="red", command=self.quit).grid(row=cur_row, column=1)

        cur_row += 1
        Label(text='Serial Output', width=15).grid(row=cur_row, column=0, sticky="E")
        self.text_field_serial_output = Text(self, height=4, width=80)
        scroll_serial_output = Scrollbar(self)

        scroll_serial_output.config(command=self.text_field_serial_output.yview)
        self.text_field_serial_output.config(yscrollcommand=scroll_serial_output.set)
        scroll_serial_output.grid(row=cur_row, column=1, columnspan=5, sticky=E)
        self.text_field_serial_output.grid(row=cur_row, column=1, columnspan=5)
        #self.update_gui_serial_status()
        self.request_serial_status()

        cur_row += 1
        Checkbutton(self, text="Autoconnect serial port",
                    variable=self.autoconnect_serial,
                    command=self.cb_autoconnect).grid(row=cur_row, column=0)

        #self.slogan.grid(row=1, column=0, columnspan=3)
        #self.exit.grid(row=2, column=0, columnspan=3)

    def call_ugs(self):
        print("Tkinter is easy to use!")
        call([UGS])



app = App()
app.mainloop()
print('Main app ended')
app.exiting = True
time.sleep(5)
app.pms_queue.put(None)
app.serial_command_queue.put(None)

