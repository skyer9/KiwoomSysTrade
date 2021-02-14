#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QAxContainer import QAxWidget


class LoginManager:
    def __init__(self, mainLogger, mainTrader):
        """
        자동투자시스템 로그인 매니저
        """
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.kiwoom.OnEventConnect.connect(self.doLogin)
        self.logger = mainLogger
        self.trader = mainTrader

    def login(self):
        """
        로그인 요청
        키움증권 로그인창 띄워주고, 자동로그인 설정시 바로 로그인 진행됨.
        OnEventConnect()으로 콜백 전달됨.
        :return: 1: 로그인 요청 성공, 0: 로그인 요청 실패
        """
        lRet = self.kiwoom.dynamicCall("CommConnect()")
        return lRet

    def doLogin(self, nErrCode):
        """
        로그인 결과 수신
        :param nErrCode: 0: 로그인 성공, 100: 사용자 정보교환 실패, 101: 서버접속 실패, 102: 버전처리 실패
        :return:
        """
        if nErrCode == 0:
            self.logger.info("로그인 성공")
            self.trader.doLoginSuccess()
            # self.request_thread_worker.login_status = 1
        elif nErrCode == 100:
            self.logger.warning("사용자 정보교환 실패")
        elif nErrCode == 101:
            self.logger.warning("서버접속 실패")
        elif nErrCode == 102:
            self.logger.warning("버전처리 실패")
