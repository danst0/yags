#!/usr/local/bin/python3

from tkinter import *
from subprocess import call
import threading
import queue
import time, random
import serial
import web


SISPMCTL = "/usr/local/bin/sispmctl"
RADIO_VARIABLE = {'LEDs': IntVar(), 'Controller': IntVar(), 'Spindle': IntVar()}
for key, val in RADIO_VARIABLE.items():
    val.set(1)
OUTLET_ASSIGNMENT = {'LEDs': 4, 'Controller': 3, 'Spindle': 2}

urls = (
    '/(.*)', 'hello'
)

class hello:        
    def GET(self, name):
        if not name: 
            name = 'World'
        return 'Hello, ' + name + '!'


class WebFrontend(threading.Thread):
    def __init__(self, pms_queue):
        self.__queue = pms_queue
        threading.Thread.__init__(self)
        app = web.application(urls, globals())
        
    def run(self):
        app.run()


class PMSController(threading.Thread):
    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)
        self.exiting = False
        self.current_status = [False, False, False, False]
        self.update_status()
    def run(self):
        while 1 and not self.exiting:
            item = self.__queue.get()
            if item is None:
                print('Stopping PMS Controller')
                self.exiting = True
                break # reached end of queue
            elif item is 'update':
                print('Updating current status')
                process = Popen([SISPMCTL, "-g", "all"], stdout=PIPE)
                # Results
                # sispmctl -g all
                # Accessing Gembird #0 USB device 002
                # Status of outlet 1:     off
                # Status of outlet 2:     off
                # Status of outlet 3:     off
                # Status of outlet 4:     on
                (output, err) = process.communicate()
                exit_code = process.wait()
                print(output)
                outlet_no = 0
                for line in output:
                    if line.startswith('Status'):
                        if line.find('off') != -1:
                            self.current_status[outlet_no] = False
                        else:
                            self.current_status[outlet_no] = True
                        outlet_no += 1
                for name, id in OUTLET_ASSIGNMENT.items():
                    RADIO_VARIABLEs[name].set(lambda: 1 if self.current_status[id] else 0)
            else:
                print("exec sispmctl with:", item, "started")
                call([SISPMCTL, item[0], str(item[1])])
    def update_status(self):
        if not self.exiting:
            threading.Timer(15.0, self.update_status).start()
            self.__queue.put('update')


class App(Tk):
    def button_command(self, i):
        #print('i', i)
        #print('Outlet', OUTLET_ASSIGNMENT[i])
        #print('State', RADIO_VARIABLE[i].get())
        if RADIO_VARIABLE[i].get() == 1:
            param = "-o"
        else:
            param = "-f"
        self.pms_queue.put([param, OUTLET_ASSIGNMENT[i]])
        #call([SISPMCTL, param, str(OUTLET_ASSIGNMENT[i])])


    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        #self.build_main_window()
        self.grid()


        
        text = ["LEDs", "Controller", "Spindle"]
        

        self.pms_queue = queue.Queue(0)
        PMSController(self.pms_queue, RADIO_VARIABLE, OUTLET_ASSIGNMENT).start()
        WebFrontend(self.pms_queue).start()
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



app = App()
app.mainloop()
print('Main app ended')
app.pms_queue.put(None)
#time.sleep(5)


