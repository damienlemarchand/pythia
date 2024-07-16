# -*- coding: utf-8 -*-
"""
Created on Fri May 12 17:09:01 2017

@author: dlemarchand
"""
from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date
from datetime import timedelta

from .datefilter import create_calendar,next_business_date,last_business_date



class Roll(ABC):
    def __init__(self):
        self.predecessor = None

    def roll(self, date_value):
        if self.predecessor is not None:
            return self.simple_roll(self.predecessor.roll(date_value))
        return self.simple_roll(date_value)

    @abstractmethod
    def simple_roll(self, date_value):
        pass


class EndOfYearRoll(Roll):
    def __init__(self, offset=0):
        super().__init__()
        self.offset = offset

    def simple_roll(self, date_value):
        return date(date_value.year + self.offset, 12, 31)


class EndOfQuarterRoll(Roll):
    def __init__(self, offset=0):
        super().__init__()
        self.offset = offset

    def simple_roll(self, date_value):
        ts = timedelta(days=1)
        e = date_value + ts
        m = 3
        if e.month > 3:
            m = 6
        if e.month > 6:
            m = 9
        if e.month > 9:
            m = 12
        last_day = monthrange(e.year, m)[1]
        eoq = date(e.year, m, last_day)
        if self.offset == 0:
            return eoq
        else:
            mr = MonthRoll(3 * self.offset)
            return mr.simple_roll(eoq)


class YearRoll(Roll):
    def __init__(self, year):
        super().__init__()
        self.year = year

    def simple_roll(self, date_value):
        return date(date_value.year + self.year, date_value.month, date_value.day)


class MonthRoll(Roll):
    def __init__(self, month, keep_end_of_month=True):
        super().__init__()
        self.month = month
        self.keepEndOfMonth = keep_end_of_month

    def add_month(self, date_value):
        m = self.month
        temp = date_value
        if m > 12:
            k = m // 12
            m = m - (12 * k)
            temp = date(k + temp.year, temp.month, temp.day)
        lm = m + temp.month
        if lm > 12:
            lm = lm - 12
            temp = date(1 + temp.year, lm, temp.day)
        else:
            temp = date(temp.year, temp.month + m, temp.day)
        return temp

    def simple_roll(self, date_value):
        if not self.keepEndOfMonth:
            return self.add_month(date_value)
        else:
            new_date = self.add_month(date_value)
            last_day = monthrange(date_value.year, date_value.month)[1]
            end_of_month = (last_day == date_value.day)
            if end_of_month:
                last_day = monthrange(new_date.year, new_date.month)[1]
                new_date = date(new_date.year, new_date.month, last_day)
            return new_date


class CalendarDayRoll(Roll):
    def __init__(self, offset=0):
        super().__init__()
        self.offset = offset

    def simple_roll(self, date_value):
        ts = timedelta(days=self.offset)
        return date_value + ts


class FollowingRoll(Roll):
    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def simple_roll(self, date_value):
        return next_business_date(self.filters, date_value)


class ModifiedFollowingRoll(Roll):
    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def simple_roll(self, date_value):
        new_date = next_business_date(self.filters, date_value)
        if new_date.month == date_value.month:
            return new_date
        else:
            last_business_date(self.filters, date_value)


def build_one_roll(token, calendars_dict=None):
    pos = 0
    status = 0
    word = ""
    sign = ""
    function_name = ""
    numeric_part = ""
    calendars = ""
    for current in token:
        concat = True
        sign_position = False
        if pos == 0:
            if (current == '+') or (current == '-'):
                sign = current
                concat = False
                sign_position = True
        if (not sign_position) and (not current.isnumeric()) and (status == 0):
            if word:
                numeric_part = word
                word = ""
            status = 1
        if (current == '[') and (status == 1) and word:
            function_name = word
            word = ""
            status = 2
            concat = False
        if (current == ']') and status == 2 and word:
            calendars = word
            word = ""
            concat = False
            status = 0
        if concat:
            word = word + current
        pos = pos + 1
    if status == 1:
        function_name = word
    if status == 2:
        calendars = word
    numeric_parameter = 0
    local_calendar = None
    if calendars:
        if calendars_dict:
            if calendars in calendars_dict:
                local_calendar = calendars_dict[calendars]
        if not local_calendar:
            local_calendar = create_calendar(calendars)
        if not local_calendar:
            raise TypeError("invalid calendar " + calendars)
    if numeric_part:
        if sign:
            numeric_part = sign + numeric_part
        else:
            numeric_part = '+' + numeric_part
        numeric_parameter = int(numeric_part)
    if function_name:
        if function_name.upper() == 'FOLLOWING':
            return FollowingRoll(local_calendar)
        if function_name.upper() == 'MODIFIEDFOLLOWING':
            return ModifiedFollowingRoll(local_calendar)
        if function_name.upper() == 'D':
            return CalendarDayRoll(numeric_parameter)
        if function_name.upper() == 'M':
            return MonthRoll(numeric_parameter)
        if function_name.upper() == 'Y':
            return YearRoll(numeric_parameter)
        if function_name.upper() == 'EOQ':
            return EndOfQuarterRoll(numeric_parameter)
        if function_name.upper() == 'EOY':
            return EndOfYearRoll(numeric_parameter)
    raise TypeError("unknown roll " + token)


# Global dictionary used as a cache for already built roll
existingRoll = {}


def build_roll(template, use_cache=True, calendars_dict=None):
    if use_cache:
        if template in existingRoll:
            return existingRoll[template]
    roll = None
    tokens = template.split('|')
    for token in tokens:
        current = build_one_roll(token, calendars_dict)
        if roll is not None:
            current.predecessor = roll
        roll = current
    if use_cache:
        existingRoll[template] = roll
    return roll


if __name__ == "__main__":
    dr = build_roll("EOQ")
    dt = date(2017, 4, 20)
    dt1 = dr.roll(dt)
    dr = build_roll("1M")
    print(dr)
    dt = date(2017,2,28)
    dt2 = dr.roll(dt)
    print(dt2)
