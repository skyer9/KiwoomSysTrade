#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import threading
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from time import sleep

from PyQt5.QtWidgets import QApplication

import config
from database import Base, StockBasicInfo, StockDayCandleChart, Session, DATABASE
from trader import KWTrader

3
COMMON_DELAY = 2.0
LONG_DELAY = 20.0
SCREEN_NUMBER = "1010"

IS_TEST_MODE = True

if IS_TEST_MODE:
    # STOCK_ACCOUNT_NUMBER = "8888888811"
    STOCK_ACCOUNT_NUMBER = config.TEST_STOCK_ACCOUNT_NUMBER  # 계좌정보가 8자리이면 끝에 11 을 붙여 10자리로 만든다.
    # LOG_LEVEL = logging.DEBUG
    LOG_LEVEL = logging.INFO
else:
    # STOCK_ACCOUNT_NUMBER = "1234567890"
    STOCK_ACCOUNT_NUMBER = config.REAL_STOCK_ACCOUNT_NUMBER
    LOG_LEVEL = logging.DEBUG

# Timestamp for loggers
formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')

# 로그 파일 핸들러
fh_log = TimedRotatingFileHandler('logs/log', when='midnight', encoding='utf-8', backupCount=120)
fh_log.setFormatter(formatter)

# stdout handler
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)

# 로거 생성 및 핸들러 등록
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
logger.addHandler(fh_log)
logger.addHandler(stdout_handler)


def run_thread():
    # 로그인 체크

    while True:
        connect_state = trader.get_connect_state()
        if connect_state is not None:
            if connect_state == 0:
                sleep(COMMON_DELAY)
                continue
        else:
            sleep(COMMON_DELAY)
            continue
        break

    request_trade_balloon = False
    while True:
        if len(trader.stock_list) > 0:
            break
        else:
            if not request_trade_balloon:
                request_trade_balloon = True
                # 거래량급증
                trader.logger.info('거래량급증요청')
                trader.request_trade_balloon('001', '2', '1', '50', '5', '9', '0', 0, SCREEN_NUMBER)
        sleep(COMMON_DELAY)

    while True:
        for stock_code in trader.stock_list:
            # 주식기본정보
            session = Session()
            item = session.query(StockBasicInfo).filter(StockBasicInfo.종목코드 == stock_code).first()
            if item is not None:
                delta = (datetime.now() - item.lastupdate)
                if delta.days == 0:
                    # 업데이트 불필요
                    # print('skip 종목명(종목코드) : %s(%s)' % (trader.get_master_code_name(stock_code), stock_code))
                    continue
            trader.logger.info('기본정보 종목명(종목코드) : %s(%s)' % (trader.get_master_code_name(stock_code), stock_code))
            trader.request_stock_basic_info(stock_code, 0, SCREEN_NUMBER)
            Session.remove()
            sleep(COMMON_DELAY)

        for stock_code in trader.stock_list:
            # 주식일봉차트
            yesterday = datetime.now() - timedelta(days=1)
            yesterday = yesterday.strftime("%Y%m%d")

            session = Session()
            item = session.query(StockDayCandleChart)\
                .filter(StockDayCandleChart.종목코드 == stock_code)\
                .order_by(StockDayCandleChart.일자.desc()).first()
            if item is not None:
                delta = (datetime.now() - item.lastupdate)
                if delta.days == 0:
                    # 업데이트 불필요
                    print('skip 종목명(종목코드) : %s(%s)' % (trader.get_master_code_name(stock_code), stock_code))
                    continue
            trader.logger.info('일봉 종목명(종목코드) : %s(%s)' % (trader.get_master_code_name(stock_code), stock_code))
            trader.request_day_candle_chart(stock_code, yesterday, 1, 0, SCREEN_NUMBER)
            Session.remove()
            sleep(COMMON_DELAY * 5)

        break


if __name__ == '__main__':
    Base.metadata.create_all(DATABASE)

    app = QApplication(sys.argv)

    trader = KWTrader()
    trader.initialize(logger)

    trader.login()

    trader.setup()

    # trader.run()
    x = threading.Thread(target=run_thread, args=())
    x.start()
    # run_thread()

    # # 종목명
    # print(trader.get_master_code_name('300120'))

    # 계좌수익률요청
    # trader.request_account_profit(STOCK_ACCOUNT_NUMBER, 0, SCREEN_NUMBER)

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

    # trader.request_call_price('300120', 2, SCREEN_NUMBER)
    #
    # trader.disconnect_real_data(SCREEN_NUMBER)

    # trader.send_order("주문", SCREEN_NUMBER, STOCK_ACCOUNT_NUMBER, 1, "034830", 1, 2100, "00", "")
    # trader.send_order("주문", SCREEN_NUMBER, STOCK_ACCOUNT_NUMBER, 2, "034830", 4, 2100, "00", "")

    sys.exit(app.exec_())
