#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from time import sleep

from PyQt5.QtWidgets import QApplication

from core import KWCore
from trader import KWTrader

SCREEN_NUMBER = "1010"

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # kw = KWCore()
    #
    # kw.comm_connect()
    #
    # ACCNO = kw.get_login_info("ACCNO")
    #
    # # print(kw.get_connect_state())
    #
    # print(kw.get_master_code_name("300120"))

    trader = KWTrader()
    trader.initialize()

    trader.connection()

    # sleep(5.0)

    print(trader.get_master_code_name('300120'))

    # ACCNO = trader.get_login_info("ACCNO")
    # ACCNO = ACCNO.split(';')
    # print(ACCNO[0])

    result = trader.opt10001("035720", 0, SCREEN_NUMBER)
    print(result)

    # result = trader.opt10085(ACCNO[0], 0, SCREEN_NUMBER)
    # print(result)
    #
    # result = trader.opt10080('300120', 3, 1, 0, SCREEN_NUMBER)
    # print(result)
