#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import time
from collections import deque
from logging.handlers import TimedRotatingFileHandler
from threading import Lock

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject, QThread
from PyQt5.QtWidgets import QApplication

import config
import util
import account
import market
import stock

# 상수
IS_TEST_MODE = True

DELAY_SECOND = 2.0

if IS_TEST_MODE:
    # STOCK_ACCOUNT_NUMBER = "8888888811"
    STOCK_ACCOUNT_NUMBER = config.TEST_STOCK_ACCOUNT_NUMBER  # 계좌정보가 8자리이면 끝에 11 을 붙여 10자리로 만든다.
    LOG_LEVEL = logging.DEBUG
else:
    # STOCK_ACCOUNT_NUMBER = "1234567890"
    STOCK_ACCOUNT_NUMBER = config.REAL_STOCK_ACCOUNT_NUMBER
    LOG_LEVEL = logging.INFO

# 종목별매수상한 = 1000000  # 종목별매수상한 백만원
# 매수수수료비율 = 0.00015  # 매도시 평단가에 곱해서 사용
# 매도수수료비율 = 0.00015 + 0.0025  # 매도시 현재가에 곱해서 사용
SCREEN_NUMBER = "1234"

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


class SyncRequestDecorator:
    """
    키움 API 비동기 함수 데코레이터
    """

    @staticmethod
    def kiwoom_sync_request(func):
        def func_wrapper(self, *args, **kwargs):
            self.request_thread_worker.request_queue.append((func, args, kwargs))

        return func_wrapper

    @staticmethod
    def kiwoom_sync_callback(func):
        def func_wrapper(self, *args, **kwargs):
            logger.debug("키움 함수 콜백: %s %s %s" % (func.__name__, args, kwargs))
            func(self, *args, **kwargs)
            if self.request_thread_worker.request_thread_lock.locked():
                self.request_thread_worker.request_thread_lock.release()

        return func_wrapper


class RequestThreadWorker(QObject):
    def __init__(self):
        """요청 쓰레드
        """
        super().__init__()
        self.request_queue = deque()  # 요청 큐
        self.request_thread_lock = Lock()

        # 간혹 요청에 대한 결과가 콜백으로 오지 않음
        # 마지막 요청을 저장해 뒀다가 일정 시간이 지나도 결과가 안오면 재요청
        self.retry_timer = None

        self.login_status = 0

    def retry(self, request):
        logger.debug("키움 함수 재시도: %s %s %s" % (request[0].__name__, request[1], request[2]))
        self.request_queue.appendleft(request)

    def run(self):
        while True:
            if self.login_status == 0:
                # 로그인 이전
                logger.debug("로그인 이전")
                time.sleep(DELAY_SECOND)
                continue

            # 큐에 요청이 있으면 하나 뺌
            # 없으면 블락상태로 있음
            try:
                logger.debug("큐 확인")
                request = self.request_queue.popleft()
            except IndexError:
                time.sleep(DELAY_SECOND)
                continue

            # 요청 실행
            logger.debug("키움 함수 실행: %s %s %s" % (request[0].__name__, request[1], request[2]))
            request[0](trader, *request[1], **request[2])

            # 요청에대한 결과 대기
            if not self.request_thread_lock.acquire(blocking=True, timeout=5):
                # 요청 실패
                time.sleep(DELAY_SECOND)
                logger.debug("요청 재시도")
                self.retry(request)  # 실패한 요청 재시도

            time.sleep(DELAY_SECOND)  # 0.2초 이상 대기 후 마무리


class SysTrader:
    def __init__(self):
        """
        자동투자시스템 메인 클래스
        """
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        # 계좌 관리자
        self.account = account.AccountManager(logger, self, STOCK_ACCOUNT_NUMBER, SCREEN_NUMBER)

        # 마켓 모니터
        self.market = market.MarketMonitor(logger, self, SCREEN_NUMBER)

        # 주식 모니터
        self.stock = stock.StockMonitor(logger, self, SCREEN_NUMBER)

        # 로그인 결과 수신
        self.kiwoom.OnEventConnect.connect(self.processLogin)

        # 요청결과 수신
        self.kiwoom.OnReceiveTrData.connect(self.kiwoom_OnReceiveTrData)

        # 실시간 메시지 수신
        self.kiwoom.OnReceiveRealData.connect(self.kiwoom_OnReceiveRealData)

        self.kiwoom.OnReceiveConditionVer.connect(self.processConditionList)
        self.kiwoom.OnReceiveTrCondition.connect(self.processConditionListChange)
        self.kiwoom.OnReceiveRealCondition.connect(self.kiwoom_OnReceiveRealCondition)

        self.kiwoom.OnReceiveChejanData.connect(self.kiwoom_OnReceiveChejanData)
        self.kiwoom.OnReceiveMsg.connect(self.kiwoom_OnReceiveMsg)

        # 요청 쓰레드
        self.request_thread_worker = RequestThreadWorker()
        self.request_thread = QThread()
        self.request_thread_worker.moveToThread(self.request_thread)
        self.request_thread.started.connect(self.request_thread_worker.run)
        self.request_thread.start()

        self.availableAccountPrice = -1

        self.params = {}
        self.result = {}

        self.dict_stock = {}
        self.dict_callback = {}

        self.dict_holding = None

        logger.debug("SysTrader started.")

    # -------------------------------------
    # 로그인 관련함수
    # -------------------------------------
    def login(self):
        """
        로그인 요청
        키움증권 로그인창 띄워주고, 자동로그인 설정시 바로 로그인 진행됨.
        OnEventConnect()으로 콜백 전달됨.
        :return: 1: 로그인 요청 성공, 0: 로그인 요청 실패
        """
        lRet = self.kiwoom.dynamicCall("CommConnect()")
        return lRet

    @SyncRequestDecorator.kiwoom_sync_callback
    def processLogin(self, nErrCode):
        """
        로그인 결과 수신
        :param nErrCode: 0: 로그인 성공, 100: 사용자 정보교환 실패, 101: 서버접속 실패, 102: 버전처리 실패
        :return:
        """
        if nErrCode == 0:
            logger.debug("로그인 성공")
            self.request_thread_worker.login_status = 1
        elif nErrCode == 100:
            logger.debug("사용자 정보교환 실패")
        elif nErrCode == 101:
            logger.debug("서버접속 실패")
        elif nErrCode == 102:
            logger.debug("버전처리 실패")

    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_GetConnectState(self):
        """
        로그인 상태 확인
        OnEventConnect 콜백
        :return: 0: 연결안됨, 1: 연결됨
        """
        lRet = self.kiwoom.dynamicCall("GetConnectState()")
        return lRet

    def kiwoom_SetInputValue(self, sID, sValue):
        """
        :param sID:
        :param sValue:
        :return:
        """
        res = self.kiwoom.dynamicCall("SetInputValue(QString, QString)", [sID, sValue])
        return res

    def kiwoom_GetRepeatCnt(self, sTRCode, sRQName):
        """
        :param sTRCode:
        :param sRQName:
        :return:
        """
        res = self.kiwoom.dynamicCall("GetRepeatCnt(QString, QString)", sTRCode, sRQName)
        return res

    def kiwoom_GetCommData(self, sTRCode, sRQName, nIndex, sItemName):
        """
        :param sTRCode:
        :param sRQName:
        :param nIndex:
        :param sItemName:
        :return:
        """
        res = self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)", sTRCode, sRQName, nIndex,
                                      sItemName)
        return res

    def kiwoom_CommRqData(self, sRQName, sTrCode, nPrevNext, sScreenNo):
        """
        :param sRQName:
        :param sTrCode:
        :param nPrevNext:
        :param sScreenNo:
        :return:
        """
        res = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)",
                                      [sRQName, sTrCode, nPrevNext, sScreenNo])
        return res

    @SyncRequestDecorator.kiwoom_sync_request
    def requestBalance(self):
        self.account.requestBalance()

    @SyncRequestDecorator.kiwoom_sync_request
    def requestBasicStockInfo(self, strCode):
        self.stock.requestBasicStockInfo(strCode)

    @SyncRequestDecorator.kiwoom_sync_request
    def requestMinuteCandleChart(self, strCode, tick=1, fix=1, size=240, nPrevNext=0):
        self.stock.requestMinuteCandleChart(strCode, tick, fix, size, nPrevNext)

    @SyncRequestDecorator.kiwoom_sync_request
    def requestDayCandleChart(self, strCode, tick=1, fix=1, size=240, nPrevNext=0):
        self.stock.requestDayCandleChart(strCode, tick, fix, size, nPrevNext)

    @SyncRequestDecorator.kiwoom_sync_request
    def requestMarketDayCandleChart(self, strCode, size=240, nPrevNext=0):
        self.market.requestMarketDayCandleChart(strCode, size, nPrevNext)

    @SyncRequestDecorator.kiwoom_sync_request
    def requestAccountProfit(self):
        self.account.requestProfit()

    @SyncRequestDecorator.kiwoom_sync_request
    def requestBuyGigwan(self, strCode, refDate):
        self.stock.requestBuyGigwan(strCode, refDate)

    @SyncRequestDecorator.kiwoom_sync_callback
    def kiwoom_OnReceiveTrData(self, sScrNo, sRQName, sTRCode, sRecordName, sPreNext, nDataLength, sErrorCode, sMessage, sSPlmMsg, **kwargs):
        """TR 요청에 대한 결과 수신
        데이터 얻어오기 위해 내부에서 GetCommData() 호출
          GetCommData(
          BSTR strTrCode,       // TR 이름
          BSTR strRecordName,   // 레코드이름
          long nIndex,          // TR 반복부
          BSTR strItemName)     // TR 에서 얻어오려는 출력항목이름
        :param sScrNo: 화면번호
        :param sRQName: 사용자 구분명
        :param sTRCode: TR이름
        :param sRecordName: 레코드 이름
        :param sPreNext: 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
        :param nDataLength: 사용안함
        :param sErrorCode: 사용안함
        :param sMessage: 사용안함
        :param sSPlmMsg: 사용안함
        :param kwargs:
        :return:
        """

        if sRQName == "예수금상세현황요청":
            self.account.processBalance(sTRCode, sRQName)

        elif sRQName == "계좌수익률요청":
            self.processAccountProfit(sRQName, sTRCode)

        elif sRQName == "주식기본정보":
            self.stock.processStockBasicInfo(sTRCode, sRQName)

        elif sRQName == "주식분봉차트조회" or sRQName == "주식일봉차트조회":
            if sRQName == "주식분봉차트조회":
                self.processMinuteCandleChart(sRQName, sTRCode, sPreNext)
            else:
                self.processDayCandleChart(sRQName, sTRCode, sPreNext)

        elif sRQName == "업종일봉조회":
            self.market.processMarketDayCandleChart(sRQName, sTRCode, sRecordName, sPreNext)

        elif sRQName == "주문":
            # self.processGetAccountProfit(sRQName, sTRCode)
            logger.debug("111111")
            logger.debug(sTRCode)
        elif sRQName == '종목별투자자':
            self.stock.processBuyGigwan(sTRCode, sRQName)

        else:
            logger.warning("처리되지 않은 레코드입니다. [%s]" % sRQName)

    # -------------------------------------
    # 실시간 관련함수
    # -------------------------------------
    def kiwoom_OnReceiveRealData(self, sCode, sRealType, sRealData, **kwargs):
        """
        실시간 데이터 수신
          OnReceiveRealData(
          BSTR sCode,        // 종목코드
          BSTR sRealType,    // 리얼타입
          BSTR sRealData    // 실시간 데이터 전문
          )
        :param sCode: 종목코드
        :param sRealType: 리얼타입
        :param sRealData: 실시간 데이터 전문
        :param kwargs:
        :return:
        """
        logger.debug("REAL: %s %s %s" % (sCode, sRealType, sRealData))

        if sRealType == "주식체결":
            pass

    # -------------------------------------
    # 조건검색 관련함수
    # GetConditionLoad(), OnReceiveConditionVer(), SendCondition(), OnReceiveRealCondition()
    # -------------------------------------
    @SyncRequestDecorator.kiwoom_sync_request
    def requestConditionList(self):
        self.stock.requestConditionList()

    @SyncRequestDecorator.kiwoom_sync_callback
    def processConditionList(self, lRet, sMsg, **kwargs):
        self.stock.processConditionList(lRet, sMsg)

    @SyncRequestDecorator.kiwoom_sync_callback
    def processConditionListChange(self, sScrNo, strCodeList, strConditionName, nIndex, nNext, **kwargs):
        self.stock.processConditionListChange(strCodeList)

    # -------------------------------------
    # 주문 관련함수
    # OnReceiveTRData(), OnReceiveMsg(), OnReceiveChejan()
    # -------------------------------------
    @SyncRequestDecorator.kiwoom_sync_request
    def kiwoom_SendOrder(self, sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo):
        """주문
        :param sRQName: 사용자 구분명
        :param sScreenNo: 화면번호
        :param sAccNo: 계좌번호 10자리
        :param nOrderType: 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
        :param sCode: 종목코드
        :param nQty: 주문수량
        :param nPrice: 주문가격
        :param sHogaGb: 거래구분(혹은 호가구분)은 아래 참고
          00 : 지정가
          03 : 시장가
          05 : 조건부지정가
          06 : 최유리지정가
          07 : 최우선지정가
          10 : 지정가IOC
          13 : 시장가IOC
          16 : 최유리IOC
          20 : 지정가FOK
          23 : 시장가FOK
          26 : 최유리FOK
          61 : 장전시간외종가
          62 : 시간외단일가매매
          81 : 장후시간외종가
        :param sOrgOrderNo: 원주문번호입니다. 신규주문에는 공백, 정정(취소)주문할 원주문번호를 입력합니다.
        :return:
        """
        logger.debug("주문: %s %s %s %s %s %s %s %s %s" % (
            sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo))
        lRet = self.kiwoom.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                                       [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb,
                                        sOrgOrderNo])
        logger.debug("kiwoom_SendOrder.lRet: {}".format(lRet))

    def kiwoom_OnReceiveRealCondition(self, strCode, strType, strConditionName, strConditionIndex, **kwargs):
        """
        실시간 조건검색 결과 수신(목록 요청 수신 후 변경이 발생한 경우)
          OnReceiveRealCondition(
          BSTR strCode,   // 종목코드
          BSTR strType,   //  이벤트 종류, "I":종목편입, "D", 종목이탈
          BSTR strConditionName,    // 조건식 이름
          BSTR strConditionIndex    // 조건명 인덱스
          )
        :param strCode: 종목코드
        :param strType: 이벤트 종류, "I":종목편입, "D", 종목이탈
        :param strConditionName: 조건식 이름
        :param strConditionIndex: 조건명 인덱스
        :param kwargs:
        :return:
        """
        logger.debug("실시간 조건검색: %s %s %s %s" % (strCode, strType, strConditionName, strConditionIndex))
        if strType == "I":
            # 모니터링 종목 리스트에 추가
            logger.debug("종목추가 : %s" % strCode)
        elif strType == "D":
            # 모니터링 종목 리스트에서 삭제
            logger.debug("종목이탈 : %s" % strCode)

    def kiwoom_OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg, **kwargs):
        """
        주문성공, 실패 메시지
        :param sScrNo: 화면번호
        :param sRQName: 사용자 구분명
        :param sTrCode: TR 이름
        :param sMsg: 서버에서 전달하는 메시지
        :param kwargs:
        :return:
        """
        logger.debug("메시지수신: %s %s %s %s" % (sScrNo, sRQName, sTrCode, sMsg))

    def kiwoom_OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList, **kwargs):
        """주문접수, 체결, 잔고발생시
        :param sGubun: 체결구분 접수와 체결시 '0'값, 국내주식 잔고전달은 '1'값, 파생잔고 전달은 '4"
        :param nItemCnt:
        :param sFIdList:
        "9201" : "계좌번호"
        "9203" : "주문번호"
        "9001" : "종목코드"
        "913" : "주문상태"
        "302" : "종목명"
        "900" : "주문수량"
        "901" : "주문가격"
        "902" : "미체결수량"
        "903" : "체결누계금액"
        "904" : "원주문번호"
        "905" : "주문구분"
        "906" : "매매구분"
        "907" : "매도수구분"
        "908" : "주문/체결시간"
        "909" : "체결번호"
        "910" : "체결가"
        "911" : "체결량"
        "10" : "현재가"
        "27" : "(최우선)매도호가"
        "28" : "(최우선)매수호가"
        "914" : "단위체결가"
        "915" : "단위체결량"
        "919" : "거부사유"
        "920" : "화면번호"
        "917" : "신용구분"
        "916" : "대출일"
        "930" : "보유수량"
        "931" : "매입단가"
        "932" : "총매입가"
        "933" : "주문가능수량"
        "945" : "당일순매수수량"
        "946" : "매도/매수구분"
        "950" : "당일총매도손일"
        "951" : "예수금"
        "307" : "기준가"
        "8019" : "손익율"
        "957" : "신용금액"
        "958" : "신용이자"
        "918" : "만기일"
        "990" : "당일실현손익(유가)"
        "991" : "당일실현손익률(유가)"
        "992" : "당일실현손익(신용)"
        "993" : "당일실현손익률(신용)"
        "397" : "파생상품거래단위"
        "305" : "상한가"
        "306" : "하한가"
        :param kwargs:
        :return:
        """
        logger.debug("체결/잔고: %s %s %s" % (sGubun, nItemCnt, sFIdList))
        if sGubun == '0':
            list_item_name = ["계좌번호", "주문번호", "관리자사번", "종목코드", "주문업무분류",
                              "주문상태", "종목명", "주문수량", "주문가격", "미체결수량",
                              "체결누계금액", "원주문번호", "주문구분", "매매구분", "매도수구분",
                              "주문체결시간", "체결번호", "체결가", "체결량", "현재가",
                              "매도호가", "매수호가", "단위체결가", "단위체결량", "당일매매수수료",
                              "당일매매세금", "거부사유", "화면번호", "터미널번호", "신용구분",
                              "대출일"]
            list_item_id = [9201, 9203, 9205, 9001, 912,
                            913, 302, 900, 901, 902,
                            903, 904, 905, 906, 907,
                            908, 909, 910, 911, 10,
                            27, 28, 914, 915, 938,
                            939, 919, 920, 921, 922,
                            923]
            dict_contract = {item_name: self.kiwoom_GetChejanData(item_id).strip() for item_name, item_id in
                             zip(list_item_name, list_item_id)}

            # 종목코드에서 'A' 제거
            종목코드 = dict_contract["종목코드"]
            if 'A' <= 종목코드[0] <= 'Z' or 'a' <= 종목코드[0] <= 'z':
                종목코드 = 종목코드[1:]
                dict_contract["종목코드"] = 종목코드

            # 종목을 대기 리스트에서 제거
            # if 종목코드 in self.set_stock_ordered:
            #    self.set_stock_ordered.remove(종목코드)

            # 매수 체결일 경우 보유종목에 빈 dict 추가 (키만 추가하기 위해)
            if "매수" in dict_contract["주문구분"]:
                self.dict_holding[종목코드] = {}
            # 매도 체결일 경우 보유종목에서 제거
            else:
                self.dict_holding.pop(종목코드, None)

            logger.debug("체결: %s" % (dict_contract,))

        if sGubun == '1':
            list_item_name = ["계좌번호", "종목코드", "신용구분", "대출일", "종목명",
                              "현재가", "보유수량", "매입단가", "총매입가", "주문가능수량",
                              "당일순매수량", "매도매수구분", "당일총매도손일", "예수금", "매도호가",
                              "매수호가", "기준가", "손익율", "신용금액", "신용이자",
                              "만기일", "당일실현손익", "당일실현손익률", "당일실현손익_신용", "당일실현손익률_신용",
                              "담보대출수량", "기타"]
            list_item_id = [9201, 9001, 917, 916, 302,
                            10, 930, 931, 932, 933,
                            945, 946, 950, 951, 27,
                            28, 307, 8019, 957, 958,
                            918, 990, 991, 992, 993,
                            959, 924]
            dict_holding = {item_name: self.kiwoom_GetChejanData(item_id).strip() for item_name, item_id in
                            zip(list_item_name, list_item_id)}
            dict_holding["현재가"] = util.safe_cast(dict_holding["현재가"], int, 0)
            dict_holding["보유수량"] = util.safe_cast(dict_holding["보유수량"], int, 0)
            dict_holding["매입단가"] = util.safe_cast(dict_holding["매입단가"], int, 0)
            dict_holding["총매입가"] = util.safe_cast(dict_holding["총매입가"], int, 0)
            dict_holding["주문가능수량"] = util.safe_cast(dict_holding["주문가능수량"], int, 0)

            # 종목코드에서 'A' 제거
            종목코드 = dict_holding["종목코드"]
            if 'A' <= 종목코드[0] <= 'Z' or 'a' <= 종목코드[0] <= 'z':
                종목코드 = 종목코드[1:]
                dict_holding["종목코드"] = 종목코드

            # 보유종목 리스트에 추가
            self.dict_holding[종목코드] = dict_holding

            logger.debug("잔고: %s" % (dict_holding,))

    def kiwoom_GetChejanData(self, nFid):
        """
        OnReceiveChejan()이벤트 함수가 호출될때 체결정보나 잔고정보를 얻어오는 함수입니다.
        이 함수는 반드시 OnReceiveChejan()이벤트 함수가 호출될때 그 안에서 사용해야 합니다.
        :param nFid: 실시간 타입에 포함된FID
        :return:
        """
        res = self.kiwoom.dynamicCall("GetChejanData(int)", [nFid])
        return res

    def processMinuteCandleChart(self, sRQName, sTRCode, sPreNext):
        self.stock.processMinuteCandleChart(sRQName, sTRCode, sPreNext)

    def processDayCandleChart(self, sRQName, sTRCode, sPreNext):
        self.stock.processDayCandleChart(sRQName, sTRCode, sPreNext)

    def processAccountProfit(self, sRQName, sTRCode):
        self.account.processAccountProfit(sRQName, sTRCode)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    trader = SysTrader()

    # 로그인
    trader.login()

    # # 계좌 잔액
    # trader.requestBalance()
    #
    # # 수익률 요청
    # trader.requestAccountProfit()
    #
    # # 업종일봉조회
    # # 업종코드 (001: 코스피, 002: 대형주, 003: 중형주, 004: 소형주, 101: 코스닥, 201: 코스피200, 302: KOSTAR, 701: KRX100)
    # trader.requestMarketDayCandleChart("001", size=480)
    # # trader.requestMarketDayCandleChart("101", size=480)
    #
    # # 주식 기본정보
    # trader.requestBasicStockInfo("035720")
    #
    # # 종목별투자자
    # trader.requestBuyGigwan("035720", "20210210")
    #
    # # 분봉조회
    # trader.requestMinuteCandleChart("035720")
    # trader.requestMinuteCandleChart("035720", size=480)
    #
    # # 일봉조회
    # trader.requestDayCandleChart("035720")
    # trader.requestDayCandleChart("035720", size=480)

    # 조건검색 리스트 요청
    trader.requestConditionList()

    # sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo
    # nOrderType: 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
    # trader.kiwoom_SendOrder("주문", 화면번호, STOCK_ACCOUNT_NUMBER, 1, "000140", 1, 1000, "00", "")

    sys.exit(app.exec_())
