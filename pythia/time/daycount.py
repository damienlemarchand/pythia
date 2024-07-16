# -*- coding: utf-8 -*-
"""
Created on Sat May 13 08:58:26 2017

@author: dlemarchand
"""

import calendar
from abc import ABC, abstractmethod
from datetime import date


class DayCountConvention(ABC):
    @abstractmethod
    def count(self, first, end):
        pass
    

class DayCountConventionISDA(DayCountConvention):
    def __init__(self, method):
        self.method = method
    
    def count(self, first, end):
        time = end-first
        y1 = float(first.year)
        y2 = float(end.year)
        m1 = float(first.month)
        m2 = float(end.month)
        d1 = float(first.day)
        d2 = float(end.day)
        if self.method == "1/1":
            return 1.0
        if self.method == "1/4":
            return 0.25
        if self.method == "1/12":
            return 1.0/12.0
        if self.method == "1/2":
            return 0.5
        if (self.method == "Act/365") or (self.method == "Actual/365"):
            dd = float(time.days)
            return dd/float(365)
        if (self.method == "Act/360") or (self.method == "Actual/360"):
            dd = float(time.days)
            return dd/float(360)
        if (self.method == "Act/365.25") or (self.method == "Actual/365.25"):
            dd = float(time.days)
            return dd/365.25
        if (self.method == "30/360") or (self.method == "Bond Basis"):
            if first.day == 31:
                d1 = float(30)
            if (end.day == 31) and (first.day > 29):
                d2 = float(30)
            num = (360.0*(y2-y1))+(30.0*(m2-m1))+(d2-d1)
            return num/float(360)
        if (self.method == "Act/Act") or (self.method == "Actual/Actual"):
            den_leap = 0
            den_not_leap = 0
            dem = 365
            num = float(time.days)
            if y1 == y2:
                if calendar.isleap(first.year):
                    dem = 366
                return num/float(dem)
            eoy = date(first.year, 12, 31)
            t1 = eoy-first
            if calendar.isleap(first.year):
                den_leap = float(t1.days)
            else:
                den_not_leap = float(t1.days)
            eoy = date(1+eoy.year, 12, 31)
            delta = end-eoy
            while delta.days > 0:
                if calendar.isleap(eoy.year):
                    den_leap = den_leap+366
                else:
                    den_not_leap = den_not_leap+365
                eoy = date(1+eoy.year, 12, 31)
                delta = end-eoy
            if eoy.year == end.year:
                boy = date(eoy.year, 1, 1)
                t1 = end-boy
                if calendar.isleap(boy.year):
                    den_leap = den_leap+float(t1.days)
                else:
                    den_not_leap = den_not_leap+float(t1.days)
            return (den_leap/float(366)) + (den_not_leap/float(365))


if __name__ == "__main__":
    dt1 = date(2012, 1, 15)
    dt2 = date(2015, 4, 10)
    dcc = DayCountConventionISDA("Act/Act")
    print(dcc.count(dt1, dt2))
