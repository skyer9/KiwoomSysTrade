#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util

class AccountManager:
    def __init__(self, __mainLogger, __sysTrader, __ACCOUNT_NUMBER, __SCREEN_NUMBER):
        """
        자동투자시스템 계좌 매니저
        """
        self.sysTrader = __sysTrader
        self.logger = __mainLogger

        self.dict_holding = None

        self.ACCOUNT_NUMBER = __ACCOUNT_NUMBER
        self.SCREEN_NUMBER = __SCREEN_NUMBER

    def requestBalance(self):
        """
        예수금 상세현황 요청
        :return:
        """
        self.sysTrader.kiwoom_SetInputValue("계좌번호", self.ACCOUNT_NUMBER)
        self.sysTrader.kiwoom_CommRqData("예수금상세현황요청", "opw00001", 0, self.SCREEN_NUMBER)

    def processBalance(self, sTRCode, sRQName):
        price = int(self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, "주문가능금액"))
        self.logger.debug("주문가능금액 : %s" % price)

    def requestProfit(self):
        """계좌수익률요청
        :return:
        """
        self.sysTrader.kiwoom_SetInputValue("계좌번호", self.ACCOUNT_NUMBER)
        res = self.sysTrader.kiwoom_CommRqData("계좌수익률요청", "opt10085", 0, self.ACCOUNT_NUMBER)
        return res

    def processAccountProfit(self, sRQName, sTRCode):
        cnt = self.sysTrader.kiwoom_GetRepeatCnt(sTRCode, sRQName)

        assert self.dict_holding is None  # The request will set this to None.
        result = {}
        for nIdx in range(cnt):
            list_item_name = ["종목코드", "종목명", "현재가", "매입가", "보유수량"]
            dict_holding = {item_name: self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name).strip() for
                            item_name in list_item_name}
            dict_holding["현재가"] = util.safe_cast(dict_holding["현재가"], int, 0)
            # 매입가를 총매입가로 키변경
            dict_holding["총매입가"] = util.safe_cast(dict_holding["매입가"], int, 0)
            dict_holding["보유수량"] = util.safe_cast(dict_holding["보유수량"], int, 0)
            dict_holding["수익"] = (dict_holding["현재가"] - dict_holding["총매입가"]) * dict_holding["보유수량"]
            stock_code = dict_holding["종목코드"]
            result[stock_code] = dict_holding
            self.logger.debug("계좌수익: %s" % (dict_holding,))

        # self.dict_holding = result
        # if '계좌수익률요청' in self.dict_callback:
        #     self.dict_callback['계좌수익률요청'](self.dict_holding)
