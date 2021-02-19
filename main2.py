#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from time import sleep

from PyQt5.QtWidgets import QApplication

from core import KWCore
from trader import KWTrader

COMMON_DELAY = 2.0
SCREEN_NUMBER = "1010"

if __name__ == '__main__':
    app = QApplication(sys.argv)

    trader = KWTrader()
    trader.initialize()

    trader.connection()

    # while trader.response_connect_status is None:
    #     sleep(1.0)

    # sleep(15.0)

    # # 종목명
    # print(trader.get_master_code_name('300120'))

    # 계좌번호
    # ACCNO = trader.get_login_info("ACCNO")
    # ACCNO = ACCNO.split(';')
    # print(ACCNO[0])

    # 계좌수익률요청
    # result = trader.opt10085(ACCNO[0], 0, SCREEN_NUMBER)
    # print(result)
    #

    # 계좌잔고조회

    # print(trader.get_connect_state)
    # while trader.get_connect_state == 0:
    #     print('2222222')
    #     sleep(1.0)

    # 주식기본정보
    # result = trader.opt10001("035720", 0, SCREEN_NUMBER)
    trader.request_stock_basic_info("035720", 0, SCREEN_NUMBER)
    # print(result)

    # # 종목별투자자기관별요청
    # result = trader.opt10059('20210218', "035720", 1, 0, 1000, 0, SCREEN_NUMBER)
    # print(result)

    # # 분봉
    # result = trader.opt10080('300120', 3, 1, 0, SCREEN_NUMBER)
    # print(result)
    # # 일봉
    # result = trader.opt10081('300120', "20200101", 1, 0, SCREEN_NUMBER)
    # print(result)
    # # 주봉
    # result = trader.opt10082('300120', "20200101", "20210218", 1, 0, SCREEN_NUMBER)
    # print(result)

    # # 업종일봉조회요청
    # result = trader.opt20006('001', "20200101", 0, SCREEN_NUMBER)
    # print(result)

    # sleep(COMMON_DELAY)
    # trader.disconnect_real_data(SCREEN_NUMBER)

    app.exec_()
