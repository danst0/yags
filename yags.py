#!/usr/bin/env python3

from tkinter import *
from subprocess import call, Popen, PIPE
import threading
import queue
import time, random
import serial
import bottle
import sys,os




SISPMCTL = "/usr/local/bin/sispmctl"
OUTLET_ASSIGNMENT = {'LEDs': 4, 'Controller': 3, 'Spindle': 2}

pms_queue = queue.Queue()

class WebFrontend(threading.Thread):
    def __init__(self, RADIO_VARIABLE):
        self.__queue = pms_queue
        self.radio_variable = RADIO_VARIABLE
        threading.Thread.__init__(self)
        self.server = None
        self.exiting = False
        print('Initializing Server')
        bottle.route('/hello/<name>')(self.hello)
        bottle.route('/')(self.index)
        bottle.route('/switch_show_status/<ident>/<on_off>')(self.send_on_off_pms_redirect)
        bottle.route('/switch/<ident>/<on_off>')(self.send_on_off_pms_no_redirect)                
    def button_command(self, ident, on_off):
        if on_off.lower() == 'on':
            param = "-o"
        else:
            param = "-f"
        self.__queue.put([param, OUTLET_ASSIGNMENT[ident]])
        self.__queue.put('update')
        
    
    def hello(self, name):
        return bottle.template('<b>Hello {{name}}</b>!', name=name)

    #@bottle.route('/')
    def index(self):
        status = {}
        for name, state in self.radio_variable.items():
            if state == 1:
                status[name] = 'On' 
            else:
                status[name] = 'Off'
        return bottle.template('pms', outlets=OUTLET_ASSIGNMENT.keys(), status=status)

    #@bottle.route('/switch_show_status/<ident>/<on_off>')
    def send_on_off_pms_redirect(self, ident, on_off):
        self.__queue.put((ident, on_off))
        return bottle.template('switch', ident=ident, on_off=on_off, redirect=True)

    def send_on_off_pms_no_redirect(self, ident, on_off):
        self.__queue.put((ident, on_off))
        return bottle.template('switch', ident=ident, on_off=on_off, redirect=False)
    def run(self):
        while not self.exiting:
            self.server = bottle.run(host='localhost', port=8081)
            print(self.server)
        print('Last words from WebFrontend')            
    def stop(self):
        self.exiting = True
        #self.server.shutdown()


class PMSController(threading.Thread):
    def __init__(self, RADIO_VARIABLE):
        self.__queue = pms_queue
        threading.Thread.__init__(self)
        self.exiting = False
        self.current_status = [False, False, False, False]
        self.update_status()
        self.radio_variable = RADIO_VARIABLE
    def run(self):
        while not self.exiting:
            try:
                item = self.__queue.get(True, timeout=1)
            except queue.Empty:
                item = None
            #print('Current item in queue', item)
            if item is 'update':
                print('Updating current status')
                try:
                    process = Popen([SISPMCTL, "-g", "all"], stdout=PIPE)
                except FileNotFoundError:
                    output = 'DEMOOUTPUT Gembird #0 USB device 002\n Status of outlet 1:     off\n Status of outlet 2:     off\n Status of outlet 3:     off  \n Status of outlet 4:     on'
                # Results: sispmctl -g all
                # Accessing Gembird #0 USB device 002
                # Status of outlet 1:     off
                # Status of outlet 2:     off
                # Status of outlet 3:     off
                # Status of outlet 4:     on
                else:
                    (output, err) = process.communicate()
                    exit_code = process.wait()
                print(output)
                outlet_no = 0
                for line in output.split('\n'):
                    if line.find('Status') != -1:
                        print(line)
                        if line.find('off') != -1:
                            self.current_status[outlet_no] = False
                        else:
                            self.current_status[outlet_no] = True
                        print(line, self.current_status[outlet_no])
                        outlet_no += 1
                for name, ident in OUTLET_ASSIGNMENT.items():
                    print(self.current_status)
                    print(name, ident)
                    
                    if self.current_status[ident-1]:
                        self.radio_variable[name].set(1)
                    else:
                        self.radio_variable[name].set(2)
                    
                    print('RADIO_VARIABLE[name]', name, self.radio_variable[name].get())
                pms_queue.task_done()                    
            elif item != None:
                print("Executing SISPMCTL with parameters:", item)
                try:
                    call([SISPMCTL, item[0], str(item[1])])
                except FileNotFoundError:
                    pass
                pms_queue.task_done()
        print('Last words from PMSController')
    def update_status(self):
        if not self.exiting:
            threading.Timer(15.0, self.update_status).start()
            self.__queue.put('update')
    def stop(self):
        self.exiting = True
        


class App(Tk):
    def button_command(self, i):
        #print('i', i)
        #print('Outlet', OUTLET_ASSIGNMENT[i])
        #print('State', RADIO_VARIABLE[i].get())
        if self.RADIO_VARIABLE[i].get() == 1:
            param = "-o"
        else:
            param = "-f"
        pms_queue.put([param, OUTLET_ASSIGNMENT[i]])
        #call([SISPMCTL, param, str(OUTLET_ASSIGNMENT[i])])


    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        #self.build_main_window()
        self.grid()

        self.abc = IntVar()
        self.RADIO_VARIABLE = {'LEDs': IntVar(), 'Controller': IntVar(), 'Spindle': IntVar()}
        for key, val in self.RADIO_VARIABLE.items():
            #print(key, val)
            val.set(1)


        text = ["LEDs", "Controller", "Spindle"]
        

        
        
        cur_row = 0
        Label(text='LEDs', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.RADIO_VARIABLE['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.RADIO_VARIABLE['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Controller', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.RADIO_VARIABLE['Controller'], command=lambda: self.button_command('Controller'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.RADIO_VARIABLE['Controller'], command=lambda: self.button_command('Controller'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Spindle', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=self.RADIO_VARIABLE['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=self.RADIO_VARIABLE['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=2).grid(row=cur_row, column=2)



        cur_row += 1
        Button(self, text="Exit", fg="red", command=self.quit).grid(row=cur_row, column=1)

APP = App()

PMS_CONTROLLER = PMSController(APP.RADIO_VARIABLE)
PMS_CONTROLLER.start()
FRONTEND = WebFrontend(APP.RADIO_VARIABLE)
FRONTEND.start()

APP.mainloop()
print('Main app exited')

print('Waiting for PMS tasks to be finalized')
pms_queue.join()
print('Active thread count', threading.active_count())

print('Active thread count', threading.active_count())
print('Stopping PMS_Controller')
PMS_CONTROLLER.stop()



print('Active thread count', threading.active_count())
print('Stopping Webfrontend')
FRONTEND.stop()


print('Waiting for finish PMSController')
PMS_CONTROLLER.join()
print('Waiting for finish WebFrontend')
FRONTEND.join(0.5)

print('Active thread count', threading.active_count())
os._exit(os.EX_OK)