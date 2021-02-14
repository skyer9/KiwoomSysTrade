#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util


class MarketMonitor:
    def __init__(self, __mainLogger, __sysTrader, __SCREEN_NUMBER):
        """
        자동투자시스템 시장 모니터
        """
        self.result = {}
        self.sysTrader = __sysTrader
        self.logger = __mainLogger

        self.SCREEN_NUMBER = __SCREEN_NUMBER

    def requestMarketDayCandleChart(self, strCode, size=240, nPrevNext=0):
        """업종일봉조회
        :param strCode: 업종코드 (001: 코스피, 002: 대형주, 003: 중형주, 004: 소형주, 101: 코스닥, 201: 코스피200, 302: KOSTAR, 701: KRX100)
        :param size: Fetch these many candle sticks.
        :param nPrevNext:
        :return:
        """
        self.sysTrader.params['size'] = size
        self.sysTrader.kiwoom_SetInputValue("업종코드", strCode)
        res = self.sysTrader.kiwoom_CommRqData("업종일봉조회", "opt20006", nPrevNext, self.SCREEN_NUMBER)
        return res

    def processMarketDayCandleChart(self, sRQName, sTRCode, sPreNext):
        cnt = self.sysTrader.kiwoom_GetRepeatCnt(sTRCode, sRQName)

        stock_code = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, "업종코드")
        stock_code = stock_code.strip()

        done = False  # 파라미터 처리 플래그
        result = []
        cnt_acc = len(result)

        list_item_name = []
        if sRQName == '업종일봉조회':
            list_item_name = ["일자", "시가", "고가", "저가", "현재가", "거래량"]

        for nIdx in range(cnt):
            item = {'업종코드': stock_code}
            for item_name in list_item_name:
                item_value = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name)
                item_value = item_value.strip()
                item[item_name] = item_value

            # 결과는 최근 데이터에서 오래된 데이터 순서로 정렬되어 있음
            date = int(item["일자"])

            # 범위조회 파라미터 처리
            date_from = int("000000000000")
            date_to = int("999999999999")
            if date > date_to:
                continue
            elif date < date_from:
                done = True
                break

            # 개수 파라미터처리
            if cnt_acc + nIdx >= float("inf"):
                done = True
                # break

            result.append(util.convert_kv(item))

        # 차트 업데이트
        self.result['result'] = result

        if not done and cnt > 0 and sPreNext == '2':
            self.result['nPrevNext'] = 2
            self.result['done'] = False
        else:
            # 연속조회 완료
            self.logger.debug("차트 연속조회완료")
            self.result['nPrevNext'] = 0
            self.result['done'] = True

        for item in self.result['result']:
            print(" date : %s, open : %f, high : %f, low : %f, 현재가 : %s, volume : %f"
                  % (item['date'], item['open'], item['high'], item['low'], item['현재가'], item['volume']))
