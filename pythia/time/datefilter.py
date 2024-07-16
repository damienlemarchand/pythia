# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 22:08:59 2017

@author: dlemarchand
"""

import re
from abc import ABC, abstractmethod
from calendar import monthrange
from datetime import date
from datetime import timedelta

MONDAY = 0
TUESDAY = 1
WEDNESDAY = 2
THURSDAY = 3
FRIDAY = 4
SATURDAY = 5
SUNDAY = 6

JANUARY = 1
FEBRUARY = 2
MARCH = 3
APRIL = 4
MAY = 5
JUNE = 6
JULY = 7
AUGUST = 8
SEPTEMBER = 9
OCTOBER = 10
NOVEMBER = 11
DECEMBER = 12


class DateFilter(ABC):
    def __init__(self):
        pass
        
    @abstractmethod
    def filter_date(self, dt):
        pass
    

def compute_easter_day(year: int) -> date:
    """
    computes the Easter day of the corresponding year
    """
    c = int(year % 100)
    b = int(year/100)
    a = int(((5*b)+c)%19)
    beta = int((3*(b+25))/4)
    epsilon = int((3*(b+25)) % 4)
    guigui = int((8*(b+11))/25)
    h = int(((19*a)+beta-guigui) % 30)
    mu = int((a+(11*h))/319)
    j = int(((60*(5-epsilon))+c)/4)
    k = int(((60*(5-epsilon))+c) % 4)
    llambda = int(((2*j)-k-h+mu) % 7)
    n = int((h-mu+llambda+110)/30)
    q = int((h-mu+llambda+110) % 30)
    p = int((q+5-n) % 32)
    return date(year, n, p)


def compute_easter_monday(year):
    easter = compute_easter_day(year)
    ts = timedelta(days=1)
    return ts+easter


def compute_holy_friday(year):
    easter = compute_easter_day(year)
    ts = timedelta(days=-2)
    return ts+easter


def compute_ascension_thursday(year):
    easter_day = compute_easter_day(year)
    ts = timedelta(days=39)
    return ts + easter_day


def compute_pentecost(year):
    easter = compute_easter_day(year)
    ts = timedelta(days=49)
    return ts+easter


def compute_pentecost_monday(year):
    easter = compute_easter_day(year)
    ts = timedelta(days=50)
    return ts+easter


class NamedDateFilter(DateFilter):

    def __init__(self, name):
        super().__init__()
        self.name = name

    def filter_date(self, dt):
        y = dt.year
        if self.name == "EASTER":
            dr = compute_easter_day(y)
            return dr == dt
        if self.name == "EASTER MONDAY":
            dr = compute_easter_monday(y)
            return dr == dt
        if (self.name == "HOLY FRIDAY") or (self.name == "BLACK FRIDAY") or (self.name == "GOOD FRIDAY"):
            dr = compute_holy_friday(y)
            return dr == dt
        if self.name == "PENTECOST":
            dr = compute_pentecost(y)
            return dr == dt
        if self.name == "ASCENSION THURSDAY":
            dr = compute_ascension_thursday(y)
            return dr == dt
        if self.name == "PENTECOST MONDAY" or self.name == "WHIT MONDAY":
            dr = compute_pentecost_monday(y)
            return dr == dt
        if self.name == "CHRISTMAS":
            return dt.month == DECEMBER and dt.day == 25
        if self.name == "UK CHRISTMAS":
            uk_christmas = date(dt.year, DECEMBER, 25)
            if uk_christmas.weekday() == SATURDAY:
                uk_christmas = date(dt.year, DECEMBER, 27)
            if uk_christmas.weekday() == SUNDAY:
                uk_christmas = date(dt.year, DECEMBER, 26)
            return uk_christmas == dt
        if self.name == "BOXING DAY":
            boxing_day = date(dt.year, DECEMBER, 26)
            if boxing_day.weekday() == SATURDAY:
                boxing_day = date(dt.year, DECEMBER, 28)
            if boxing_day.weekday() == SUNDAY:
                boxing_day = date(dt.year, DECEMBER, 27)
            return boxing_day == dt
        if self.name == "EOM" or self.name == "END OF MONTH":
            last_day = monthrange(dt.year, dt.month)[1]
            return last_day == dt.day
        if self.name == "EOY" or self.name == "END OF YEAR":
            return dt.month == DECEMBER and dt.day == 31
        if self.name == "EOQ" or self.name == "END OF QUARTER":
            if dt.month in [MARCH, JUNE, SEPTEMBER, DECEMBER]:
                last_day = monthrange(dt.year, dt.month)[1]
                return last_day == dt.day
        return False


class SetOfDateFilter(DateFilter):

    def __init__(self, date_list):
        super().__init__()
        self.date_list = date_list

    def filter_date(self, dt):
        if dt in self.date_list:
            return True
        return False


class WeekdayFilter(DateFilter):

    def __init__(self, weekday):
        super().__init__()
        self.weekday = weekday

    def filter_date(self, dt):
        return dt.weekday() == self.weekday


class WeekdayOfMonthFilter(DateFilter):

    def __init__(self, weekday,n):
        super().__init__()
        self.weekday = weekday
        self.n = n

    def filter_date(self, dt):
        if dt.weekday() == self.weekday:
            ts = timedelta(days=7)
            i = 1
            date_value = dt - ts
            while date_value.month == dt.month:
                i = i +1
                date_value = date_value - ts
            if i == self.n:
                return True
        return False


class MonthFilter(DateFilter):

    def __init__(self, month):
        super().__init__()
        self.month = month

    def filter_date(self, dt):
        return dt.month == self.month


class BirthdayFilter(DateFilter):

    def __init__(self, day, month):
        super().__init__()
        self.day = day
        self.month = month

    def filter_date(self, dt):
        return dt.month == self.month and dt.day == self.day


class WeekdayFollowingFilter(DateFilter):

    def __init__(self, day, month, weekday):
        super().__init__()
        self.day = day
        self.month = month
        self.weekday = weekday

    def filter_date(self, dt):
        if self.month>0:
            b_day = date(dt.year, self.month, self.day)
        else:
            b_day = date(dt.year, dt.month, self.day)
        ts = timedelta(days=1)
        while b_day.weekday() != self.weekday:
            b_day = b_day + ts
        return b_day == dt


class RangeFilter(DateFilter):

    def __init__(self, start, end):
        super().__init__()
        self.start = start
        self.end = end

    def filter_date(self, dt):
        return (dt >= self.start) and (dt <= self.end)


class AndFilters(DateFilter):

    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def filter_date(self, dt):
        for filter in self.filters:
            if not filter.filter_date(dt):
                return False
        return True


class OrFilters(DateFilter):

    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def filter_date(self, dt):
        for filter in self.filters:
            if filter.filter_date(dt):
                return True
        return False


def build_date(template):
    if not template:
        return
    # yyyy-mm-dd
    pattern = "([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))"
    if re.match(pattern, template):
        year = int(template[0:4])
        month = int(template[5:7])
        day = int(template[8:10])
        return date(year, month, day)
    # dd/mm/yyyy
    pattern = "^([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))(\/)\d{4}$"
    if re.match(pattern, template):
        day = int(template[0:2])
        month = int(template[3:5])
        year = int(template[6:10])
        return date(year, month, day)


def create_filter(template):
    if not template:
        return
    tidy = template.strip().upper()
    # famous dates
    named = ["EASTER", "EASTER MONDAY",
             "HOLY FRIDAY", "BLACK FRIDAY",
             "GOOD FRIDAY", "PENTECOST",
             "PENTECOST MONDAY", "WHIT MONDAY",
             "CHRISTMAS", "UK CHRISTMAS", "BOXING DAY",
             "EOM", "END OF MONTH",
             "EOY", "END OF YEAR",
             "EOQ", "END OF QUARTER"
             ]
    if tidy in named:
        named_filter = NamedDateFilter(tidy)
        return named_filter
    # weekday
    week_str = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    if tidy in week_str:
        return WeekdayFilter(week_str.index(tidy))
    # a month
    month_str = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
                 "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
    if tidy in month_str:
        return MonthFilter(month_str.index(tidy)+1)
    # the n th weekday of a month WEEKDAY|n
    if '|' in tidy:
        item_list = tidy.split('|')
        pattern = "[1-4]"
        if len(item_list) == 2:
            if item_list[0] and item_list[1]:
                if item_list[0] in week_str and re.match(pattern, item_list[1]):
                    return WeekdayOfMonthFilter(week_str.index(item_list[0]), int(item_list[1]))
    # weekday following a birthday :  dd/MM>WEEKDAY or dd>WEEKDAY
    if '>' in tidy:
        item_list = tidy.split('>')
        pattern = "([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))"
        if len(item_list) == 2:
            if item_list[0] and item_list[1]:
                if item_list[1] in week_str and re.match(pattern, item_list[0]):
                    day = int(tidy[0:2])
                    month = int(tidy[3:5])
                    return WeekdayFollowingFilter(day, month, week_str.index(item_list[1]))
        pattern = "([0-2][0-9]|(3)[0-1])"
        if len(item_list) == 2:
            if item_list[0] and item_list[1]:
                if item_list[1] in week_str and re.match(pattern, item_list[0]):
                    day = int(tidy[0:2])
                    month = 0
                    return WeekdayFollowingFilter(day, month, week_str.index(item_list[1]))

    # ( list of filters separated by comma)
    if tidy[0] == "(" and tidy[len(tidy)-1] == ")":
        item_list = tidy[1:len(tidy)-1].split(",")
        # list of dates
        date_values = []
        for item in item_list:
            date_val = build_date(item)
            if date_val:
                date_values.append(date_val)
        if len(date_values) == len(item_list):
            return SetOfDateFilter(date_values)
        filter_list = []
        for item in item_list:
            filter_item = create_filter(item)
            if filter_item:
                filter_list.append(filter_item)
        if len(filter_list) == len(item_list):
            return AndFilters(filter_list)
    # [ date_1 ; date _2 ] a range of dates
    if tidy[0] == "[" and tidy[len(tidy) - 1] == "]":
        item_list = tidy[1:len(tidy) - 1].split(";")
        if len(item_list) == 2:
            dt_0 = build_date(item_list[0])
            dt_1 = build_date(item_list[1])
            if dt_0 and dt_1:
                if dt_1<dt_0:
                    dt_temp = dt_0
                    dt_0 = dt_1
                    dt_1 = dt_temp
                return RangeFilter(dt_0, dt_1)
    # yyyy-mm-dd or dd/mm/yyyy
    date_val = build_date(tidy)
    if date_val:
        return SetOfDateFilter([date_val])
    # dd/MM i.e birthday
    pattern = "([0-2][0-9]|(3)[0-1])(\/)(((0)[0-9])|((1)[0-2]))"
    if re.match(pattern, tidy):
        day = int(tidy[0:2])
        month = int(tidy[3:5])
        return BirthdayFilter(day, month)


def create_filters(template_list, method = "AND"):
    if not template_list:
        return
    local_list = None
    if isinstance(template_list, str):
        local_list = []
        tokens = template_list.split('+')
        for token in tokens:
            local_list.append(token)
    if isinstance(template_list, list):
        local_list = template_list
    if not local_list:
        return
    filters = []
    for template in local_list:
        local_filter = create_filter(template)
        if local_filter:
            filters.append(local_filter)
    if len(filters) == len(local_list):
        if not method:
            return AndFilters(filters)
        if method.upper() == "AND":
            return AndFilters(filters)
        if method.upper() == "OR":
            return OrFilters(filters)


def create_calendar(template_list):
    return create_filters(template_list, method="OR")


def is_business_date(filter_object, dt):
    return not filter_object.filter_date(dt)


def next_business_date(filter_object, dt):
    ts = timedelta(days=1)
    temp = dt + ts
    while not is_business_date(filter_object,temp):
        temp = temp + ts
    return temp


def last_business_date(filter_object, dt):
    ts = timedelta(days=1)
    temp = dt - ts
    while not is_business_date(filter_object,temp):
        temp = temp - ts
    return temp
