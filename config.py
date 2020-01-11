#!/usr/bin/python
# -*- coding: utf-8 -*-

from enum import Enum


db_file = "database1.vdb"


class States(Enum):
    """
    Мы используем БД Vedis, в которой хранимые значения всегда строки,
    поэтому и тут будем использовать тоже строки (str)
    """
    S_START = "0"  # Начало нового диалога
    S_YN_POST = "1"
    S_YN_TOUR = "2"
    S_ADMIN_FORWARDED_MESSAGE = "3"
    S_BUY_SUBSCRIBE = "4"
