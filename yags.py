#!/usr/local/bin/python3

from tkinter import *
from subprocess import call
import threading
import queue
import time, random
import serial

SISPMCTL = "/usr/local/bin/sispmctl"


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


    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)
        #self.build_main_window()
        self.grid()
        self.exiting = False

        self.variable = {'LEDs': IntVar(), 'Controller': IntVar(), 'Spindle': IntVar()}
        for key, val in self.variable.items():
            val.set(1)
        text = ["LEDs", "Controller", "Spindle"]
        self.outlet = {'LEDs': 4, 'Controller': 3, 'Spindle': 2}

        self.pms_queue = queue.Queue(0)
        PMSController(self.pms_queue).start()

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



        cur_row += 1
        Button(self, text="Exit", fg="red", command=self.quit).grid(row=cur_row, column=1)



app = App()
app.mainloop()
print('Main app ended')
app.exiting = True
time.sleep(5)
app.pms_queue.put(None)

