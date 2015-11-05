#!/usr/local/bin/python3

from tkinter import *
from subprocess import call
import threading
import queue
import time, random
import serial
import bottle



SISPMCTL = "/usr/local/bin/sispmctl"
RADIO_VARIABLE = {'LEDs': IntVar(), 'Controller': IntVar(), 'Spindle': IntVar()}
for key, val in RADIO_VARIABLE.items():
    val.set(1)
OUTLET_ASSIGNMENT = {'LEDs': 4, 'Controller': 3, 'Spindle': 2}

pms_queue = queue.Queue()

class WebFrontend(threading.Thread):
    def __init__(self, pms_queue):
        self.__queue = pms_queue
        threading.Thread.__init__(self)
        self.server = None
        self.exiting = False
    def button_command(self, ident, on_off):
        if on_off.lower() == 'on':
            param = "-o"
        else:
            param = "-f"
        self.__queue.put([param, OUTLET_ASSIGNMENT[ident]])
        self.__queue.put('update')
        
    @bottle.route('/hello/<name>')
    def hello(self, name):
        return bottle.template('<b>Hello {{name}}</b>!', name=name)
    
    @bottle.route('/')
    def index(self):
        status = {}
        for name, state in RADIO_VARIABLE.items():
            if state == 1:
                status[name] = 'On' 
            else:
                status[name] = 'Off'
        return bottle.template('pms', outlets=OUTLET_ASSIGNMENT.keys(), status=status)

    @bottle.route('/switch_show_status/<ident>/<on_off>')
    def send_on_off_pms_redirect(self, ident, on_off):
        self.send_on_off_pms(ident, on_off, redirect=True)
    
    
    @bottle.route('/switch/<ident>/<on_off>')
    def send_on_off_pms(self, ident, on_off, redirect=False):
        self.__queue.put(ident, on_off)
        return bottle.template('switch', ident=ident, on_off=on_off, redirect=redirect)
    
    def run(self):
        while not self.exiting:
            self.server = bottle.run(host='localhost', port=8081)
    def stop(self):
        self.exiting = True
        self.server.stop()


class PMSController(threading.Thread):
    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)
        self.exiting = False
        self.current_status = [False, False, False, False]
        self.update_status()
    def run(self):
        while not self.exiting:
            item = self.__queue.get()
            if item is 'update':
                print('Updating current status')
                process = Popen([SISPMCTL, "-g", "all"], stdout=PIPE)
                # Results: sispmctl -g all
                # Accessing Gembird #0 USB device 002
                # Status of outlet 1:     off
                # Status of outlet 2:     off
                # Status of outlet 3:     off
                # Status of outlet 4:     on
                (output, err) = process.communicate()
                exit_code = process.wait()
                print(output)
                outlet_no = 1
                for line in output:
                    if line.startswith('Status'):
                        if line.find('off') != -1:
                            self.current_status[outlet_no] = False
                        else:
                            self.current_status[outlet_no] = True
                        outlet_no += 1
                for name, id in OUTLET_ASSIGNMENT.items():
                    RADIO_VARIABLE[name].set(lambda: 1 if self.current_status[id] else 2)
                    print('RADIO_VARIABLE[name]', name, RADIO_VARIABLE[name])
            else:
                print("Executing SISPMCTL with parameters:", item)
                call([SISPMCTL, item[0], str(item[1])])
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
        if RADIO_VARIABLE[i].get() == 1:
            param = "-o"
        else:
            param = "-f"
        pms_queue.put([param, OUTLET_ASSIGNMENT[i]])
        #call([SISPMCTL, param, str(OUTLET_ASSIGNMENT[i])])


    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        #self.build_main_window()
        self.grid()


        
        text = ["LEDs", "Controller", "Spindle"]
        

        
        
        cur_row = 0
        Label(text='LEDs', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=RADIO_VARIABLE['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=RADIO_VARIABLE['LEDs'], command=lambda: self.button_command('LEDs'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Controller', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=RADIO_VARIABLE['Controller'], command=lambda: self.button_command('Controller'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=RADIO_VARIABLE['Controller'], command=lambda: self.button_command('Controller'),
                    value=2).grid(row=cur_row, column=2)

        cur_row += 1
        Label(text='Spindle', width=15).grid(row=cur_row, column=0, sticky="E")
        Radiobutton(self, text="On", padx = 20, variable=RADIO_VARIABLE['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=1).grid(row=cur_row, column=1)
        Radiobutton(self, text="Off", padx = 20, variable=RADIO_VARIABLE['Spindle'], command=lambda: self.button_command('Spindle'),
                    value=2).grid(row=cur_row, column=2)



        cur_row += 1
        Button(self, text="Exit", fg="red", command=self.quit).grid(row=cur_row, column=1)


PMS_CONTROLLER = PMSController(pms_queue, RADIO_VARIABLE, OUTLET_ASSIGNMENT).start()
FRONTEND = WebFrontend(pms_queue).start()
APP = App()
APP.mainloop()
print('Main app exited')
print('Active thread count', threading.active_count())
print('Waiting for PMS tasks to be finalized')
pms_queue.join()
print('Active thread count', threading.active_count())
print('Stopping Webfrontend')
FRONTEND.stop()
print('Waiting for finish')
FRONTEND.join()
print('Active thread count', threading.active_count())
print('Stopping PMS_Controller')
PMS_CONTROLLER.stop()
PMS_CONTROLLER.join()
print('Waiting for finish')
print('Active thread count', threading.active_count())

