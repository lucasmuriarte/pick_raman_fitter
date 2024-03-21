# -*- coding: utf-8 -*-
"""
Created on Sun Nov  6 21:14:07 2022

@author: lucas
"""
import matplotlib.pyplot as plt        
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from cursor import SnaptoCursor
from matplotlib.backends.qt_compat import is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)


class Grapth(QWidget):
    def __init__(self, figure, parent=None, toolbar=True, **kwargs):
        cursor=dict({'cursor':False,'ax':None,'y':True,'click':True,
                     'number_click':-1,'vertical_draw':True,'draw':'snap',
                     'color':False, 'click_callback': None},**kwargs)
        super().__init__(parent)
        self.figure = figure
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        self.toolbar = NavigationToolbar(self.canvas, self)
        if toolbar:    
            layout.addWidget(self.toolbar)
        self.cursor_dict=cursor
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        if cursor['cursor']:
            if cursor['ax'] is None:
                self.ax=plt.gca()
            else:
                self.ax=cursor['ax']   
            self.click_callback = cursor["click_callback"]
            line = self.ax.lines[0]
            x=line.get_xdata()
            if cursor['y']:
                 y=line.get_ydata()
            else:
                y=x*0.0
            self.cursore = SnaptoCursor(self.ax,x,y,
                                       number_click=cursor['number_click'],
                                       vertical_draw=cursor['vertical_draw'],
                                       draw=cursor['draw'],
                                       color=cursor['color'])
            def onmove(event):
                self.cursore.mouseMove(event)
                
            def onclick(event):
                if self.toolbar._active is None and cursor['click']:
                    self.cursore.onClick(event)
                    if self.click_callback:
                        if event.button==1:
                            if self.cursor_dict['y']:
                                data_x, data_y = self.cursorData()
                                self.click_callback(data_x[-1], data_y[-1])
                            else:
                                self.click_callback(data_x[-1])
                        elif event.button==3:
                            if self.cursor_dict['y']:
                                self.click_callback(None, None)
                            else: 
                                self.click_callback(None)
                            
            def onenter(event):
                self.cursore.onEnterAxes(event)
           
            def onleave(event):
                self.cursore.onLeaveAxes(event)
                
            self.canvas.mpl_connect('axes_enter_event', onenter)
            self.canvas.mpl_connect('axes_leave_event', onleave)
            self.canvas.mpl_connect('motion_notify_event', onmove)
            self.canvas.mpl_connect('button_press_event', onclick)
        self.canvas.draw()
        
    def cursorData(self):
        if self.cursor_dict['cursor'] and self.cursor_dict['y']:
            return list(set(self.cursore.datax)),list(set(self.cursore.datay))
        elif self.cursor_dict['cursor']:
            return list(set(self.cursore.datax))
 