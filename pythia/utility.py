# -*- coding: utf-8 -*-
"""
Created on 2021-06-10

"""
import re
from datetime import datetime


def to_datetime(value):
    """
    Utility function which convert a string to a datetime by guessing the format used
    If value is a datetime object, it returns it
    return None if guess failed
    """
    if value is None:
        return None
    if isinstance(value, str):
        if len(value.strip()) == 8:
            # yyyymmdd
            m = re.match('[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', value.strip())
            if m:
                return datetime.strptime(value, '%Y%m%d')
        if len(value.strip()) == 10:
            # dd/mm/yyyy
            m = re.match('[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]', value.strip())
            if m:
                return datetime.strptime(value, '%d/%m/%Y')
            # yyyy-mm-dd
            m = re.match('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]', value.strip())
            if m:
                return datetime.strptime(value, '%Y-%m-%d')
    if isinstance(value, datetime):
        return value
    return None
