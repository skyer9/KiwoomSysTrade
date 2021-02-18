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

    trader = KWTrader()
    trader.initialize()

    trader.connection()

    # 종목명
    # print(trader.get_master_code_name('300120'))

    # 계좌번호
    # ACCNO = trader.get_login_info("ACCNO")
    # ACCNO = ACCNO.split(';')
    # print(ACCNO[0])

    # 계좌수익률요청
    # result = trader.opt10085(ACCNO[0], 0, SCREEN_NUMBER)
    # print(result)
    #

    # 주식기본정보
    result = trader.opt10001("035720", 0, SCREEN_NUMBER)
    print(result)

    # # 분봉
    # result = trader.opt10080('300120', 3, 1, 0, SCREEN_NUMBER)
    # print(result)
    # # 일봉
    # result = trader.opt10081('300120', "20200101", 1, 0, SCREEN_NUMBER)
    # print(result)
    # # 주봉
    # result = trader.opt10082('300120', "20200101", "20210218", 1, 0, SCREEN_NUMBER)
    # print(result)
