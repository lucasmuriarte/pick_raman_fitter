# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 21:41:26 2022

@author: lucas
"""
import numpy as np
from scipy.optimize import curve_fit
import spe_loader as sl
import matplotlib.pyplot as plt


class LorentzianFitter:
    def __init__(self, laser_excitation=514.5, range_min=2800, range_max=3300,
                 parent=None):
        self.path: str = None
        self.wavenum: np.array = None
        self.intensity: np.array = None
        self.poptMain: list = None
        self.pcovMain: list = None

        self._range_min = range_min
        self._range_max = range_max
        self._laser_excitation = laser_excitation
        self._fitted_range = None
        
        self.parent = parent
        self.clear_data()
    
    def clear_last_fit(self):
        last_key = list(self.records.keys())[-1]
        print(last_key)
        self.records.pop(last_key)
        self.widths = self.widths.pop()
        self.centers = self.centers.pop()
        self.number_fits -= 1
        print("deleted last fit")
        
    def delete_record(self, record):
        records = list(self.records.keys())
        if record in records:
           num = records.index(record)
           self.centers.pop(num)
           self.widths.pop(num)
           self.records.pop(record)
    
    def clear_data(self):
        self.records = {}
        self.widths = []
        self.centers = []
        self.number_fits = 0
        self.data_loaded = False
        self.valid_file = False
        
    @property
    def range_min(self):
        if not self.parent:
            return self._range_min 
        return self.parent.range_min
    
    @range_min.setter
    def range_min(self, value):
        if not self.parent:
            self._range_min = value
    
    @property
    def range_max(self):
        if not self.parent:
            return self._range_max 
        return self.parent.range_max
    
    @range_max.setter
    def range_max(self, value):
        if not self.parent:
            self._range_max = value
    
    @property
    def laser_excitation(self):
        if not self.parent:
            return self._laser_excitation
        return self.parent.laser_excitation_value
    
    @laser_excitation.setter
    def laser_excitation(self, value):
        if not self.parent:
            self._laser_excitation = value
    
    def load_data(self, path):
        self.path = path
        self.wavenum, self.intensity = self._read_data()
        self.data_loaded = True
        self.valid_file = False

    def _read_data(self):
        spe_files = sl.load_from_files([self.path])
        
        wavenumber = (1/self.laser_excitation - 1/spe_files.wavelength)*10000000
        intensity = spe_files.data[0][0][0]
        return wavenumber, intensity
    
    @staticmethod    
    def lorentzian(x, a, x0, sigma):
        return (2*a/np.pi)*(sigma/(4*(x-x0)**2 + sigma**2))
    
    def fit_data(self, x0_init: int = None, width_init: int = None):
        print(1)
        print(self.range_min, self.range_max, self.laser_excitation)
        
        mini = np.argmin(abs(self.wavenum-self.range_min))
        maxi = np.argmin(abs(self.wavenum-self.range_max))
        self.valid_file = True
        if mini == maxi:
            self.valid_file = False
            print("Not valid file")
            return None
        x = self.wavenum[mini:maxi]
        y = self.intensity[mini:maxi] - np.min(self.intensity)
        if not x0_init:
            x0_init = self.range_min + (self.range_max-self.range_min)/2
        if not width_init:
            width_init = 10
        print(2)
        try:
            self.poptMain, self.pcovMain = curve_fit(self.lorentzian, x, y,
                                                 p0=(10, x0_init, width_init))
            self._fitted_range = [mini, maxi]
        except Exception as error:
            print(error)
        else:
            print(3)
            self.add_fit_to_history()
    
    def add_fit_to_history(self):
        if self.path in self.records.keys():
            print("warning not adding data file alredy exist")
            return None
        self.data_loaded = False
        self.number_fits += 1 
        self.widths.append(self.last_peak_width())
        self.centers.append(self.last_peak_center())
        record = {"wavenum": self.wavenum, "intensity":self.intensity, 
                  "fitted_range": self._fitted_range, "poptMain": self.poptMain}
        self.records[self.path] = record
        
    def last_peak_center(self):
        return self.poptMain[1]
    
    def last_peak_width(self):
        return self.poptMain[2]
    
    def get_record(self, record):
        if record == "last":
            mini, maxi, poptMain = self._fitted_range[0], self._fitted_range[1], self.poptMain
            return self.wavenum,self.intensity, self.wavenum[mini:maxi], poptMain
        if type(record) == int:
            record = list(self.records.kesy())[record]
        data = self.records.get(record, None)
        if not data:
            raise Exception("No such record found")
        mini, maxi = data["fitted_range"][0], data["fitted_range"][1]
        wave = data["wavenum"]
        return wave, data["intensity"], wave[mini:maxi], data["poptMain"]
        
    def plot_fit(self, record="last"):
        
        if self._fitted_range is None:
            print("No fit performed")
            return None
        wavenum, intensity, fitted_x, poptMain = self.get_record(record)
        fig, ax = plt.subplots(1)
        ax.plot(wavenum,intensity, label="data")
        intensity_fit = self.lorentzian(fitted_x, *poptMain) + np.min(intensity)
        ax.plot(fitted_x, intensity_fit, label='fit')
        ax.legend()
        return fig, ax