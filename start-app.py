# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 21:07:12 2022

@author: lucas
"""
from PyQt5 import QtWidgets as QW
import matplotlib.pyplot as plt
from figure_canvas import Grapth
from PyQt5.QtGui import QFont
from  PyQt5.QtCore import Qt, QThread
import sys
from  lorentzian_fitter import  LorentzianFitter
from thread_workers import GenericWorker, ContinuosFitter
import time
import re
import os
from collections import Counter
import numpy as np
from functools import partial
import pandas as pd


class VLayout(QW.QVBoxLayout):
    """
    Replace a QT vertical layout and add several methods as hide_all and
    show_all
    """
    def __init__(self, parent=None):
        super(VLayout, self).__init__(parent)
        self.added_widgets = []

    def addSeveralWidgets(self, lista):
        for i in lista:
            if type(i) is list:
                self.addWidget(i[0], *i[1:])
            else:
                self.addWidget(i)

    def addWidget(self, a0, *args):
        super().addWidget(a0, *args)
        self.added_widgets.append(a0)

    def hide_all(self):
        for i in self.added_widgets:
            i.setVisible(False)

    def show_all(self):
        for i in self.added_widgets:
            i.show()


class labelLineEdit(QW.QWidget):
    def __init__(self, label, default, tooltip=None, parent=None):
        super().__init__(parent)
        self.layout = VLayout(self)
        self.label = QW.QLabel(label)
        self.text = QW.QLineEdit(default)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)
            self.text.setToolTip(tooltip)
        
    @property
    def value(self):
        return self.text.text()

class DialogRejectAccept(QW.QMessageBox):
    def __init__(self, parent, window_title, dialog_message, accept_button="Accept",
                 reject_button="Cancel", accept_call_back=None, reject_callback=None,
                 add_cancel=False):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setText(dialog_message)
        self.reject=QW.QPushButton(reject_button, self)
        self.accept=QW.QPushButton(accept_button, self)
        self.addButton(self.reject, QW.QMessageBox.AcceptRole)
        self.addButton(self.accept, QW.QMessageBox.AcceptRole)
        self.setDefaultButton(self.accept)
        self.accept_call_back = accept_call_back
        self.reject_callback = reject_callback
        if add_cancel:
             self.cancel=QW.QPushButton("Cancel", self)
             self.addButton(self.cancel, QW.QMessageBox.AcceptRole)
    
    def exec(self):
        super().exec()
        if self.clickedButton() == self.accept:
            self.accept_call_back()
        elif self.clickedButton() == self.reject:
            self.reject_callback()
        else:
            self.close()

class labelRegion(QW.QWidget):
    def __init__(self, label, default1, default2, tooltip=None, parent=None):
        super().__init__(parent)
        self.layout = VLayout(self)
        self.label = QW.QLabel(label)
        
        self.text1 = QW.QLineEdit(default1)
        self.text2 = QW.QLineEdit(default2)
        hlayout = QW.QHBoxLayout()
        hlayout.addWidget(self.text1)
        hlayout.addWidget(QW.QLabel("-"))
        hlayout.addWidget(self.text2)
        self.layout.addWidget(self.label)
        self.layout.addLayout(hlayout)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)
            self.text1.setToolTip(tooltip)
            self.text2.setToolTip(tooltip)
        
    def get_range(self):
        return [int(self.text1.text()), int(self.text2.text())]

class spinBox(QW.QWidget):
    def __init__(self, label, mini, maxi, step=1, tooltip=None, parent=None):
        super(spinBox, self).__init__(parent)
        self.layout = VLayout(self)
        self.label = QW.QLabel(label)
        self.spin = QW.QSpinBox()
        self.spin.setMinimum(mini)
        self.spin.setMaximum(maxi)
        self.spin.setSingleStep(step)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spin)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)
            self.spin.setToolTip(tooltip)

    @property
    def value(self):
        return self.spin.value()

    @value.setter
    def value(self, value):
        return self.spin.setValue(value)

    def valueChangedConnect(self, fucnt):
        self.spin.valueChanged.connect(fucnt)

class DoubleButtonWidget(QW.QWidget):
    def __init__(self, label1, label_button1, label_button2, fun_button1, fun_button2,
                 tooltip=None, parent=None):
        super().__init__(parent)
        self.layout = VLayout(self)
        hlayout = QW.QHBoxLayout()
        self.label_1 = QW.QLabel(label1)
        self.button_1 = QW.QPushButton(label_button1)
        self.button_2 = QW.QPushButton(label_button2)
        self.button_1.clicked.connect(fun_button1)
        self.button_2.clicked.connect(fun_button2)
        hlayout.addWidget(self.button_1)
        hlayout.addWidget(self.button_2)
        self.layout.addWidget(self.label_1)
        self.layout.addLayout(hlayout)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)

class TemperatureWidget(DoubleButtonWidget):
    def __init__(self, temp_fig, temp_ax,  parent=None):
        tool_tip = 'Click on "Set file path" to set or change the path of the temperature file. \n\
Click on "Update figure" to update the temperature figure for new points.'
        super().__init__("Temperature Settings:", "Set file path", "Update figure",
                         self._set_path, self._update_figure, tool_tip, parent)
        self.temp_ax = temp_ax
        self.temp_fig = temp_fig
        self.temp_file_path = None
        self.file_labels = []
        self.temp_array = None
    
    def _set_path(self):
        path = QW.QFileDialog.getOpenFileName(self,'',"all data")
        print(path)
        self.temp_file_path = path[0]
    
    def _clear_figure(self):
        data_line = self.temp_ax.lines[0]
        data_line.set_xdata([1])
        data_line.set_ydata([1])
        self.temp_ax.relim()
        self.temp_ax.autoscale_view()
        self.temp_fig.canvas.draw_idle()
        self.temp_fig.canvas.flush_events()
    
    def read_temperatures(self):
        if not self.temp_file_path:
            return None
        df1, day_origin = self._read_temperature_file()
        df2 = self.read_name_files_readed(day_origin)
        df_merged = pd.merge_asof(df2, df1, left_on='FILES_TIMES', 
                                  right_on='TIMES')
        temps = df_merged.TEMPERATURES.str.extract("(\d+.\d+)(?= K)")
        self.temp_array = [float(val[0]) for val in temps.values.tolist()]

    
    def _update_figure(self):
        if not self.temp_file_path:
            self._set_path()
        self.read_temperatures()
        data_line = self.temp_ax.lines[0]
        x = list(range(1, len( self.temp_array) + 1))
        data_line.set_xdata(x)
       
        data_line.set_ydata(self.temp_array)
        
        extra_x = (x[-1]-x[0])*0.1
        extra_y = abs(min(self.temp_array)-max(self.temp_array))*0.1
        self.temp_ax.set_ylim(min(self.temp_array)-extra_y,
                               max(self.temp_array)+extra_y)
        self.temp_ax.set_xlim(x[0]-extra_x, x[-1]+extra_x)
        
        self.temp_ax.relim()
        self.temp_ax.autoscale_view()
        self.temp_fig.canvas.draw_idle()
        self.temp_fig.canvas.flush_events()

    def _read_temperature_file(self):
        df = pd.read_csv(self.temp_file_path, sep=",", encoding='cp1252',
                         header=None, usecols=[0, 1], names=["TIMES",
                                                             "TEMPERATURES"])
        df.TIMES = pd.to_datetime(df.TIMES, dayfirst=True)
        t = df.TIMES.iloc[0]
        day_origin = t.date().strftime("%Y-%m-%d")
        return df, day_origin

    def read_name_files_readed(self, origin):
        matches = []
        for file in self.file_labels:
            match = re.findall("\d+_\d+_\d+", file)[0]
            match = match.replace("_", ":")
            matches.append(f"{origin} {match}")
        out = pd.to_datetime(pd.Series(matches))
        df = pd.DataFrame(out, columns=["FILES_TIMES"])
        return df

class DoubleLabelWidget(QW.QWidget):
    def __init__(self, label1, label2, tooltip=None, parent=None):
        super().__init__(parent)
        self.layout = VLayout(self)
        self.label_1 = QW.QLabel(label1)
        self.label_2 = QW.QLabel(label2)
        self.layout.addWidget(self.label_1)
        self.layout.addWidget(self.label_2)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)
    
    def set_info_label(self, label, number=2):
        if number == 2:
            self.label_2.setText(f"{label}")
        else:
            self.label_1.setText(f"{label}")
    
class InfoWidget(QW.QWidget):
    def __init__(self, tooltip=None, parent=None):
        super().__init__(parent)
        self.layout = VLayout(self)
        
        self.position = DoubleLabelWidget("peak position (cm-1)", " ")
        self.width = DoubleLabelWidget("peak width  (cm-1)", " ")
        self.temperature = DoubleLabelWidget("temperature (K)", " ")
        self.layout.addWidget(QW.QLabel("Information Panel:"))
        self.layout.addWidget(self.position)
        self.layout.addWidget(self.width)
        self.layout.addWidget(self.temperature)
        self.layout.setAlignment(Qt.AlignLeft)
        if tooltip:
            QW.QToolTip.setFont(QFont('SansSerif', 10))
            self.setToolTip(tooltip)
    

class Window(QW.QMainWindow):
    def __init__(self, fitter: LorentzianFitter):
        super().__init__()
        self.fitter = fitter
        self.fitter.parent = self
        self.setWindowTitle("Raman peak-shitf finder")
        self._main = QW.QWidget()
        self.setCentralWidget(self._main)
        
        self.save_data_button = QW.QPushButton("Save fits Data")
        self.save_data_button.clicked.connect(self.save_data)
        self.clear_data_button = QW.QPushButton("Clear Data")
        self.clear_data_button.setStyleSheet("background-color : red")
        self.clear_data_button.clicked.connect(self.clear_data)
        self.button_start = QW.QPushButton("Start")
        self.button_stop = QW.QPushButton("Stop")
        self.button_path =  QW.QPushButton("Set path")
        self.button_start.clicked.connect(self._start)
        self.button_stop.clicked.connect(self._stop)
        self.button_path.clicked.connect(self._path)
        self.region = labelRegion("fitting region (cm-1)", "2800", "3800",
                                  "range where to fit the Lorentzian function")
        
        tip = "how many seconds to wait before next refresh"
        self.freq_import = spinBox("update frequency (s)", 1, 60, 1, tip)
        
        self.fit_selector = QW.QComboBox()
        self.fit_selector.addItem("None")
        self.fit_selector.activated.connect(self.update_fit_fig)
        
        self.info_panel = InfoWidget()
        self.figure_pos, self.ax_pos = plt.subplots(1, figsize=(8,8))
        self.ax_pos.set_title("peak position")
        self.ax_pos.set_ylabel(r"Raman shift (cm$^{-1}$)")
        self.ax_pos.set_xlabel("Spectrum number")
        
        self.figure_width, self.ax_width = plt.subplots(1, figsize=(8,8))
        self.ax_width.set_title("peak width")
        self.ax_width.set_ylabel(r"Raman shift (cm$^{-1}$)")
        self.ax_width.set_xlabel("Spectrum number")
        
        self.figure_fit, self.ax_fit = plt.subplots(1, figsize=(8,8))
        self.ax_fit.set_xlabel(r"Raman shift cm$^{-1}$")
        self.ax_fit.set_ylabel("Intensity (A.U.)")
        self.figure_temp, self.ax_temp = plt.subplots(1, figsize=(8,8))
        self.ax_temp.set_ylabel("Temperature (K)")
        self.ax_temp.set_xlabel("Spectrum number")
        
        self.working_path = None
        self.temperature_buttons = TemperatureWidget(self.figure_temp, 
                                                     self.ax_temp)
        
        self.set_figure_lines()
        self.set_figure_spots()
        
        self.laser_excitation = spinBox("Laser Excitation", 100, 1500, 1, 
                                        "Enter the Raman excitation Wavelenght")
        self.laser_excitation.value = 514.5
        self._running = False        
        self.fitting_thread = QThread()
        self.fitting_thread.start(QThread.TimeCriticalPriority)
        self.load_data = False
        
        self._counter = Counter()
        
        self.running_status = QW.QCheckBox("running status")
        self.running_status.setCheckState(2)
        self.running_status.setStyleSheet("QCheckBox::indicator"
                    "{background-color : red;}")
        
        self.fitter_scheduler = ContinuosFitter(int(self.freq_import.value))
        self.fitter_scheduler.valueChanged.connect(self._run_fit)
        
        self.set_app_layout()        
    
    def set_figure_lines(self):
        self.position_line = self.ax_pos.plot([1], [1], marker="o")
        self.width_line = self.ax_width.plot([1], [1], marker="o")
        self.data_line = self.ax_fit.plot([1], [1], label="data")
        self.fit_line = self.ax_fit.plot([1], [1], label="fit")
        self.temp_line = self.ax_temp.plot([1], [1], marker="o")

    def set_figure_spots(self):
        self.pos_red_spot = self.ax_pos.plot([], [], marker="o", c="lime",
                                             markeredgecolor='k', markersize=10)
        self.width_red_spot = self.ax_width.plot([], [], marker="o", c="lime",
                                                 markeredgecolor='k', markersize=10)
        self.temp_red_spot = self.ax_temp.plot([], [], marker="o", c="lime",
                                               markeredgecolor='k', markersize=10)
    
    def set_app_layout(self):
        left_panel = QW.QVBoxLayout()
        left_panel.setAlignment(Qt.AlignTop)
        left_panel.addWidget(self.button_path)
        left_panel.addWidget(self.laser_excitation)
        left_panel.addWidget(self.freq_import)
        left_panel.addWidget(self.region)
        left_panel.addWidget(self.fit_selector)
        left_panel.addWidget(self.save_data_button)
        left_panel.addWidget(self.clear_data_button)
        left_panel.addWidget(self.temperature_buttons)
        left_panel.addWidget(self.info_panel)
        
        
        def pass_info_cursor(x, y, name):
            atribute = getattr(self.info_panel, name)
            if y:
                atribute.set_info_label(y)
            else:
                atribute.set_info_label("")
                
        width_callback = partial(pass_info_cursor, name="width")
        temp_callback = partial(pass_info_cursor, name="temperature")
        pos_callback = partial(pass_info_cursor, name="position")
        
        width_fig = Grapth(self.figure_width, self._main, toolbar=True, 
                           cursor=True, click=True, ax=self.ax_width, 
                           click_callback=width_callback, number_click=1)
        pos_fig = Grapth(self.figure_pos, self._main, toolbar=True, 
                           cursor=True, click=True, ax=self.ax_pos,
                           click_callback=pos_callback, number_click=1)
        
        fit_fig = Grapth(self.figure_fit, self._main, toolbar=True, 
                         cursor=False, click=False, ax=self.ax_fit)
        temp_fig = Grapth(self.figure_temp, self._main, toolbar=True, 
                          cursor=True, click=1, ax=self.ax_temp,
                          click_callback=temp_callback, number_click=1)
        

        figure_layout_all = QW.QVBoxLayout()
        figure_layout = QW.QHBoxLayout()
        figure_layout.addWidget(pos_fig)
        figure_layout.addWidget(width_fig)
        
        figure_layout2 = QW.QHBoxLayout()
        figure_layout2.addWidget(fit_fig)
        figure_layout2.addWidget(temp_fig)
        
        figure_layout_all.addLayout(figure_layout)
        figure_layout_all.addLayout(figure_layout2)
        
        top_layout = QW.QHBoxLayout()
        top_layout.addLayout(left_panel)
        top_layout.addLayout(figure_layout_all)
        
        start_stop_layout = QW.QHBoxLayout()
        start_stop_layout.setContentsMargins(300, 0, 180, 0)
        start_stop_layout.addWidget(self.button_start)
        start_stop_layout.addWidget(self.button_stop)
        start_stop_layout.addWidget(self.running_status)
        
        self.layout = QW.QVBoxLayout(self._main)
        self.layout.addLayout(top_layout)
        self.layout.addLayout(start_stop_layout)
      
    @property
    def laser_excitation_value(self):
        return float(self.laser_excitation.value)
    
    @property
    def range_max(self):
        return float(self.region.get_range()[1])
    
    @property
    def range_min(self):
        return float(self.region.get_range()[0])
    
    def clear_data(self):
        msg = "The current fits will be deleted, please make sure you dont lose \
        any important information, since data cannot be recovered. If not you may want to save the data first" 
        save_delete = partial(self.save_data, delete_after=True)
        message = DialogRejectAccept(self, "deleting data", msg, 
                                     "Save and delete data", "delete data", 
                                     save_delete, self._clear_data, True)
        message.exec()
    
    def _clear_data(self):
        self.fit_selector.clear()
        self.fit_selector.addItem("None")
        self.temperature_buttons.file_labels = []
        self.temperature_buttons.readed_files = []
        self.temperature_buttons._clear_figure()
        self._update_fit_fig_clear()
        self.fitter.clear_data()
        self._update_plots()
    
    def save_data(self, delete_after=False):
        name_saved_file = QW.QFileDialog.getSaveFileName(self, 'save data',
                                                         "experiment file")
        print(name_saved_file)
        data = {"files": list(self.fitter.records.keys()),
                "peak_psotion (cm-1)": self.fitter.centers,
                "peak_widths (cm-1)": self.fitter.widths}
        print(1)
        if self.temperature_buttons.temp_file_path:
            self.temperature_buttons.read_temperatures()
            data["temperature (K)"] = self.temperature_buttons.temp_array
        print(2)
        df = pd.DataFrame(data)
        print(3)
        path = name_saved_file[0]
        if not path.endswith(".csv"):
            path = path + '.csv'
        print(4)
        df.to_csv(path)
    
    
    def _update_fit_fig_clear(self):
        self.data_line[0].set_xdata([1])
        self.data_line[0].set_ydata([1])
        self.fit_line[0].set_xdata([1])
        self.fit_line[0].set_ydata([1])
        self.ax_fit.relim()
        self.ax_fit.autoscale_view()
        self.figure_fit.canvas.draw_idle()
        self.figure_fit.canvas.flush_events()
    
    def delete_resatrt_spots(self):
        self.pos_red_spot[0].remove()
        self.width_red_spot[0].remove()
        self.temp_red_spot[0].remove()
        self.set_figure_spots()
        self._draw_pos_width_temp_fig()

    
    def add_red_spots_width_pos_figs(self, name):
        if name == "None":
            self.delete_resatrt_spots()
            return None
        index = self.fit_selector.findText(name) - 1
        x_pos = index+1
        width = self.fitter.widths[index]
        pos = self.fitter.centers[index]    
        self.width_red_spot[0].set_xdata(x_pos)
        self.width_red_spot[0].set_ydata(width)
        
        self.pos_red_spot[0].set_xdata(x_pos)
        self.pos_red_spot[0].set_ydata(pos)
        
        self.figure_width.canvas.flush_events()
        self.figure_pos.canvas.flush_events()
        self.figure_pos.canvas.draw_idle()
        self.figure_width.canvas.draw_idle()
        if self.temperature_buttons.temp_array:
            if len(self.temperature_buttons.temp_array) >= x_pos:
                self.temp_red_spot[0].set_xdata(x_pos)
                temp = self.temperature_buttons.temp_array[x_pos-1]
                self.temp_red_spot[0].set_ydata(temp)
            else:
                self.temp_red_spot[0].remove()
                self.temp_red_spot = self.ax_temp.plot([], [], marker="o", c="lime",
                                                markeredgecolor='k', markersize=10)
            self.figure_temp.canvas.flush_events()
            self.figure_temp.canvas.draw_idle()
                
            
    def update_fit_fig(self):

        name = self.fit_selector.currentText()
        self.add_red_spots_width_pos_figs(name)
        if name == "None":
            self.data_line[0].set_xdata([1])
            self.data_line[0].set_ydata([1])
            
            self.fit_line[0].set_xdata([1])
            self.fit_line[0].set_ydata([1])
            self.ax_fit.set_title("")
        else:
            key = os.path.join(window.working_path, name)
            datas = self.fitter.get_record(key)
            
            self.data_line[0].set_xdata(datas[0])
            self.data_line[0].set_ydata(datas[1])
            
            intensity_fit = self.fitter.lorentzian(datas[2], *datas[3]) + np.min(datas[1])
            
            self.fit_line[0].set_xdata(datas[2])
            self.fit_line[0].set_ydata(intensity_fit)
            
            self.ax_fit.set_title(name)
            
        self.ax_fit.legend()
        
        self.ax_fit.relim()
        self.ax_fit.autoscale_view()

        self.figure_fit.canvas.draw_idle()
        self.figure_fit.canvas.flush_events()
        
    def _path(self):
        text = 'Select a directory'
        self.working_path = QW.QFileDialog.getExistingDirectory(self, text,
                                                                'all data')
        
        used_file_path = os.path.join(self.working_path, "used_files")
        self.temperature_buttons.working_path = used_file_path
        if not  os.path.exists(used_file_path):
            os.mkdir(used_file_path)
        
    def _start(self):
        if not self.working_path:
            msg = 'Use "Set Path" button to define the folder where files are found'
            mesage = QW.QMessageBox()
            mesage.setWindowTitle('Error message')
            mesage.setText(msg)
            mesage.exec()
        else:
            print("start")
            if not self._running:
                self._running = True
                self.fitter_scheduler.start()
                print(self.fitter_scheduler.running)
            self.update_visual_status()
        
    def _test_thread(self):
        print("hello")

    def _stop(self):
        print("stop")
        if self._running:
            self._running = False
            self.fitter_scheduler.running = False
            self.fitter_scheduler.quit()
            self.fitter_scheduler.wait()
        self.update_visual_status()
    
    def update_visual_status(self):
        if self._running:
              self.running_status.setStyleSheet("QCheckBox::indicator"
                                                "{background-color : lightgreen;}")
        else:
            self.running_status.setStyleSheet("QCheckBox::indicator"
                                              "{background-color : red;}")
    
    def _run_fit(self):       
        path = self._look_for_data()
        if not path:
            return None
        
        self._counter.update({path: 1})
        if self._counter[path] > 5:
            print(f"rerunning thread: {self.fitter.data_loaded}")
            self.load_data = False
            
        if self.load_data:
            if self.fitter.data_loaded:
                return None
        self.load_data = True
        print("path", path)
        my_worker = GenericWorker(self._fit_data, path=path)
        my_worker.moveToThread(self.fitting_thread)
        my_worker.start.emit("start")
        my_worker.finished.connect(self._fit_finished)
    
    def _fit_finished(self):
        print("finished")
        path_split = os.path.split(self.fitter.path)
        destination = os.path.join(path_split[0], "used_files", path_split[-1])
        try:
            os.rename(self.fitter.path, destination)
            self.update_fitted_selector()
        except FileExistsError as error:
            self.error_file_exist(error)
        else:
            print(self.fitter.poptMain)
            self.load_data = False
            self._update_plots()
    
    def error_file_exist(self, error: FileExistsError):
        print(self.fitter.widths)
        if self._running:
            self._stop()
            time.sleep(1)
            msg = f"please clean the folder {self.working_path}/used_files, the following error occur: \n\n"
            msg = msg + str(error)
            mesage = QW.QMessageBox()
            mesage.setWindowTitle('Error message')
            mesage.setText(msg)
            mesage.exec()
        self.fitter.clear_last_fit()
        
        
    def update_fitted_selector(self):
        if self.fitter.valid_file:
            name = os.path.split(self.fitter.path)[-1]
            self.fit_selector.addItem(name)
            self.temperature_buttons.file_labels.append(name)
            
    def _fit_data(self, path):
        self.fitter.load_data(path)
        self.fitter.fit_data()
    
    def _update_plots(self):
        if len(self.fitter.widths) > 0:    
            x = list(range(1, len(self.fitter.widths) + 1)) 
        else:
            x = []
        self.width_line[0].set_xdata(x)
        self.width_line[0].set_ydata(self.fitter.widths)
        self.position_line[0].set_xdata(x)
        self.position_line[0].set_ydata(self.fitter.centers)
        if x:
            self.set_figures_limits(x)
            
        self.ax_pos.relim()
        self.ax_pos.autoscale_view()
        self._draw_pos_width_temp_fig()
    
    def set_figures_limits(self, x):
        extra_x = (x[-1]-x[0])*0.1
        extra_y = abs(min(self.fitter.widths)-max(self.fitter.widths))*0.1
        self.ax_width.set_ylim(min(self.fitter.widths)-extra_y,
                               max(self.fitter.widths)+extra_y)
        self.ax_width.set_xlim(x[0]-extra_x, x[-1]+extra_x)
        
        self.ax_width.autoscale_view()
        self.ax_width.relim()
        
        extra = abs(min(self.fitter.centers)-max(self.fitter.centers))*0.1
        self.ax_pos.set_ylim(min(self.fitter.centers)-extra,
                               max(self.fitter.centers)+extra)
        self.ax_pos.set_xlim(x[0]-extra_x, x[-1]+extra_x)
    
    def _draw_pos_width_temp_fig(self):
        self.figure_temp.canvas.draw_idle()
        self.figure_temp.canvas.flush_events()
        self.figure_pos.canvas.draw_idle()
        self.figure_width.canvas.draw_idle()
        self.figure_width.canvas.flush_events()
        self.figure_pos.canvas.flush_events()
        print("figures updated")
        
    def _look_for_data(self):
        files = os.listdir(self.working_path)
        file_return = None
        for file in files:
            if file.endswith(".spe"):
                file_return = file
                break
            else:
                file_return = None

        if file_return is not None:    
            return os.path.join(self.working_path, file_return)
        
            
if __name__ == '__main__':
    App = QW.QApplication(sys.argv)
    plt.ioff()
    fitter = LorentzianFitter(514.5, 2800, 3300)
    # create the instance of our Window
    window = Window(fitter)
    window.show()

    # start the app
    sys.exit(App.exec())