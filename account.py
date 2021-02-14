#!/usr/bin/env python
# -*- coding: utf-8 -*-


class AccountManager:
    def __init__(self, __mainLogger, __sysTrader, __ACCOUNT_NUMBER, __SCREEN_NUMBER):
        """
        자동투자시스템 로그인 매니저
        """
        self.sysTrader = __sysTrader
        self.logger = __mainLogger

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
