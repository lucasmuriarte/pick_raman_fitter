# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 22:06:24 2022

@author: lucas
"""
from PyQt5.QtCore import  pyqtSignal, pyqtSlot, QObject, QThread


class ContinuosFitter(QThread):
    valueChanged = pyqtSignal(float)

    def __init__(self, waiting_time):
        super().__init__()
        self.waiting_time = waiting_time
        self.running = False
        print("thread created")
        # print(self.time_steps, 'hola')

    def run(self):
        self.running = True
        print("thread start")
        while self.running:
            self.sleep(self.waiting_time)  # value set  by try and error
            self.valueChanged.emit(1)


class GenericWorker(QObject):
    """
    Class that is use to create threads
    """

    start = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super(GenericWorker, self).__init__()
        #        logthread('GenericWorker.__init__')
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start.connect(self.run)
        self.isRunning = False

    start = pyqtSignal(str)

    @pyqtSlot()
    def run(self):
        print('start fitting')
        self.isRunning = True
        self.function(*self.args, **self.kwargs)
        self.finished.emit()
        self.isRunning = False