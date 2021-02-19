#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from time import sleep

from PyQt5.QtWidgets import QApplication

from core import KWCore
from trader import KWTrader

COMMON_DELAY = 2.0
LONG_DELAY = 20.0
SCREEN_NUMBER = "1010"

if __name__ == '__main__':
    app = QApplication(sys.argv)

    trader = KWTrader()
    trader.initialize()

    trader.connection()

    # # 종목명
    # print(trader.get_master_code_name('300120'))

    # 계좌번호
    # ACCNO = trader.get_login_info("ACCNO")
    # ACCNO = ACCNO.split(';')
    # print(ACCNO[0])

    # 계좌수익률요청
    # trader.request_account_profit('8159006411', 0, SCREEN_NUMBER)

    # 계좌잔고조회

    # 주식기본정보
    # trader.request_stock_basic_info("035720", 0, SCREEN_NUMBER)

    # 종목별투자자기관별요청
    # trader.request_buy_gigwan('20210218', "035720", 1, 0, 1000, 0, SCREEN_NUMBER)

    # 분봉
    # trader.request_minute_candle_chart('300120', 3, 1, 0, SCREEN_NUMBER)
    # 일봉
    # trader.request_day_candle_chart('300120', "20200101", 1, 0, SCREEN_NUMBER)
    # 주봉
    # trader.request_week_candle_chart('300120', "20200101", "20210218", 1, 0, SCREEN_NUMBER)

    # 업종일봉조회요청
    # trader.request_upjong_day_candle_chart('001', "20200101", 0, SCREEN_NUMBER)

    trader.request_call_price('300120', 2, SCREEN_NUMBER)

    # sleep(LONG_DELAY)

    # trader.disconnect_real_data(SCREEN_NUMBER)

    sys.exit(app.exec_())
