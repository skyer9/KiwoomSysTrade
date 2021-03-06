#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import deque
from datetime import datetime
from threading import Lock
from time import sleep

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QObject, QThread

import database
from constants import KWErrorCode
from database import StockBasicInfo, StockDayCandleChart, Session

DELAY_SECOND = 2.0
DELAY_SECOND_SHORT = 1.0


class ScreenNumberManager:
    _instance = None

    @classmethod
    def _getInstance(cls):
        return cls._instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls._instance = cls(*args, **kargs)
        cls.instance = cls._getInstance
        return cls._instance

    def __init__(self):
        self._screen_number = 1

    def get_screen_number(self):
        res = str(self._screen_number).zfill(4)
        self._screen_number += 1
        if self._screen_number > 50:    # 최대 화면갯수는 200개이다.
            self._screen_number = 1
        return res


class SyncRequestDecorator:
    @staticmethod
    def sync_request(func):
        def func_wrapper(self, *args, **kwargs):
            self.request_thread_worker.request_queue.append((func, args, kwargs))

        return func_wrapper

    @staticmethod
    def sync_callback(func):
        def func_wrapper(self, *args, **kwargs):
            # print("키움 함수 콜백: %s %s %s" % (func.__name__, args, kwargs))
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

        self.trader = None

    def retry(self, request):
        print("키움 함수 재시도: %s %s %s" % (request[0].__name__, request[1], request[2]))
        self.request_queue.appendleft(request)

    def run(self):
        while True:
            if self.login_status == 0:
                # 로그인 이전
                self.trader.logger.debug("로그인 이전")
                sleep(DELAY_SECOND)
                continue

            # while database.DB_LOCKED:
            #     self.trader.logger.debug('database in use')
            #     sleep(0.3)

            # 큐에 요청이 있으면 하나 뺌
            # 없으면 블락상태로 있음
            try:
                self.trader.logger.debug("큐 확인")
                request = self.request_queue.popleft()
            except IndexError:
                sleep(DELAY_SECOND)
                continue

            # 요청 실행
            # print("키움 함수 실행: %s %s %s" % (request[0].__name__, request[1], request[2]))
            self.trader.logger.debug("키움 함수 호출 실행: %s %s %s" % (request[0].__name__, request[1], request[2]))
            request[0](self.trader, *request[1], **request[2])


def get_data_from_single_comm_data(commData, lst):
    res = {}
    for i, header in enumerate(commData['comm_data']['single']['header']):
        for col in lst:
            if header == col:
                res[col] = commData['comm_data']['single']['rows'][i]

    return res


def get_data_from_multiple_comm_data(commData, lst):
    res = []
    for row in commData['comm_data']['multiple']['rows']:
        item = {}
        for i, header in enumerate(commData['comm_data']['multiple']['header']):
            for col in lst:
                if header == col:
                    item[col] = row[i]
        res.append(item)

    return res


class KWCore(QAxWidget):
    tr_list = {}

    def __init__(self):
        super().__init__()

        assert (self.setControl("KHOPENAPI.KHOpenAPICtrl.1"))
        self._init_connect_events()
        self.response_comm_rq_data = None
        self.account_number = None
        self.logger = None
        self.available_price = None
        self.stock_list = []

    def _init_connect_events(self):
        # 서버 접속 관련 이벤트
        self.OnEventConnect.connect(self.on_event_connect)

        # 서버통신 후 데이터를 받은 시점을 알려준다.
        self.receive_tr_data_handler = {}
        self.OnReceiveTrData.connect(self.on_receive_tr_data)

        # 실시간데이터를 받은 시점을 알려준다.
        self.OnReceiveRealData.connect(self.on_receive_real_data)

        # 서버통신 후 메시지를 받은 시점을 알려준다.
        self.OnReceiveMsg.connect(self.on_receive_msg)

        # 체결데이터를 받은 시점을 알려준다.
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)

        # 조건검색 실시간 편입,이탈 종목을 받을 시점을 알려준다.
        self.OnReceiveRealCondition.connect(self.on_receive_condition)

        # 조건검색 조회응답으로 종목리스트를 구분자(";")로 붙어서 받는 시점.
        self.OnReceiveTrCondition.connect(self.on_receive_tr_condition)

        # 로컬에 사용자 조건식 저장 성공 여부를 확인하는 시점
        self.OnReceiveConditionVer.connect(self.on_receive_condition_ver)

        # 요청 쓰레드
        self.request_thread_worker = RequestThreadWorker()
        self.request_thread_worker.trader = self
        self.request_thread = QThread()
        self.request_thread_worker.moveToThread(self.request_thread)
        self.request_thread.started.connect(self.request_thread_worker.run)
        self.request_thread.start()

    def comm_connect(self):
        """
        원형 : LONG CommConnect()
        설명 : 로그인 윈도우 실행
        반환값 : 0 - 성공, 음수값은 실패
        비고 : 로그인이 성공하거나 실패하는 경우 OnEventConnect 이벤트가 발생하고 이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.
        """
        self.logger.info('로그인 요청')
        res = self.dynamicCall("CommConnect()")
        return res

    @SyncRequestDecorator.sync_callback
    def on_event_connect(self, err_code):
        """
        원형 : void OnEventConnect(LONG nErrCode);
        설명 : 서버 접속 관련 이벤트
        입력값 : LONG nErrCode : 에러 코드
        반환값 : 없음
        비고 :
            nErrCode가 0이면 로그인 성공, 음수면 실패
            음수인 경우는 에러 코드 참조
        """
        self.logger.debug('로그인 결과 수신')

        if err_code == KWErrorCode.OP_ERR_NONE:
            self.logger.info('로그인 성공')

            # # 계좌정보
            # account_number = self.get_login_info('ACCNO')
            # account_number = account_number.split(';')
            # self.account_number = account_number

            self.request_thread_worker.login_status = 1
        else:
            self.logger.info('로그인 실패')

    def get_login_info(self, tag):
        """
        원형 : BSTR GetLoginInfo(BSTR sTag)
        설명 : 로그인한 사용자 정보를 반환한다.
        입력값 : BSTR sTag : 사용자 정보 구분 TAG값 (비고)
        반환값 : TAG값에 따른 데이터 반환
        비고 :
            BSTRsTag에 들어 갈 수 있는 값은 아래와 같음
            "ACCOUNT_CNT" – 전체 계좌 개수를 반환한다.
            "ACCNO" – 전체 계좌를 반환한다. 계좌별 구분은 ';'이다.
            "USER_ID" - 사용자 ID를 반환한다.
            "USER_NAME" – 사용자명을 반환한다.
            "KEY_BSECGB" – 키보드보안 해지여부. 0:정상, 1:해지
            "FIREW_SECGB" – 방화벽 설정 여부. 0:미설정, 1:설정, 2:해지
            Ex) openApi.GetLoginInfo("ACCOUNT_CNT");
        """
        return self.dynamicCall("GetLoginInfo(QString)", tag)

    def get_connect_state(self):
        """
        원형 : LONG GetConnectState()
        설명 : 현재접속상태를 반환한다.
        입력값 : 없음
        반환값 : 접속상태
        비고 : 0:미연결, 1:연결완료
        """
        return self.dynamicCall("GetConnectState()")

    def get_master_code_name(self, code):
        """
        원형 : BSTR GetMasterCodeName(LPCTSTR strCode)
        설명 : 종목코드의 한글명을 반환한다.
        입력값 : strCode – 종목코드
        반환값 : 종목한글명
        비고 : 장내외, 지수선옵, 주식선옵 검색 가능.
        """
        return self.dynamicCall("GetMasterCodeName(QString)", code)

    @SyncRequestDecorator.sync_request
    def request_stock_basic_info(self, code, prev_next, screen_no):
        return self.tr_list['opt10001'].tr_opt(code, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_minute_candle_chart(self, code, tick_range, fix, prev_next, screen_no):
        return self.tr_list['opt10080'].tr_opt(code, tick_range, fix, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_day_candle_chart(self, code, date_from, input2, prev_next, screen_no):
        return self.tr_list['opt10081'].tr_opt(code, date_from, input2, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_week_candle_chart(self, code, date_from, date_to, input3, prev_next, screen_no):
        return self.tr_list['opt10082'].tr_opt(code, date_from, date_to, input3, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_upjong_day_candle_chart(self, input0, input1, prev_next, screen_no):
        return self.tr_list['opt20006'].tr_opt(input0, input1, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_buy_gigwan(self, date, code, input2, input3, input4, prev_next, screen_no):
        return self.tr_list['opt10059'].tr_opt(date, code, input2, input3, input4, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_account_profit(self, account_no, prev_next, screen_no):
        return self.tr_list['opt10085'].tr_opt(account_no, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_call_price(self, code, prev_next, screen_no):
        return self.tr_list['opt10004'].tr_opt(code, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def request_account_balance(self):
        account_no = self.account_number[0]
        prev_next = 0
        screen_number = ScreenNumberManager.instance().get_screen_number()
        self.logger.info("screen_number : %s" % screen_number)

        return self.tr_list['opw00001'].tr_opt(account_no, prev_next, screen_number)

    @SyncRequestDecorator.sync_request
    def request_trade_balloon(self, market_type, sort_type, time_type, trade_type,
                              minutes, jongmok_type, price_type, prev_next, screen_no):
        return self.tr_list['opt10023'].tr_opt(market_type, sort_type, time_type, trade_type,
                                               minutes, jongmok_type, price_type, prev_next, screen_no)

    @SyncRequestDecorator.sync_request
    def setup(self):
        # 계좌정보
        account_number = self.get_login_info('ACCNO')
        account_number = account_number.split(';')
        self.account_number = account_number
        self.logger.debug('계좌정보 : %s' % self.account_number)

        # 예수금상세현황
        self.request_account_balance()

    @SyncRequestDecorator.sync_request
    def send_order(self, rq_name, screen_no, account_no, order_type, code, qty, price, hoga_gb, org_order_no):
        """
        원형 : LONG SendOrder(
                BSTR sRQName,
                BSTR sScreenNo,
                BSTR sAccNo,
                LONG nOrderType,
                BSTR sCode,
                LONG nQty,
                LONG nPrice,
                BSTR sHogaGb, BSTR sOrgOrderNo
            )
        설명 : 주식 주문을 서버로 전송한다.
        입력값 :
            sRQName - 사용자 구분 요청 명
            sScreenNo - 화면번호[4]
            sAccNo - 계좌번호[10]
            nOrderType - 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
            sCode, - 주식종목코드
            nQty – 주문수량
            nPrice – 주문단가
            sHogaGb - 거래구분
            sOrgOrderNo – 원주문번호
        반환값 : 에러코드 <4.에러코드표 참고>
        비고 :
            sHogaGb – 00:지정가, 03:시장가, 05:조건부지정가, 06:최유리지정가, 07:최우선지정가, 10:지정 가IOC, 13:시장가IOC,
            16:최유리IOC, 20:지정가FOK, 23:시장가FOK, 26:최유리FOK, 61:장전시간 외종가, 62:시간외단일가, 81:장후시간외종가
            ※ 시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시 간외, 장후시간외 주문시 주문가격을 입력하지 않습니다.
            Ex) 지정가 매수 - openApi.SendOrder("RQ_1", "0101", "5015123410", 1, "000660", 10, 48500, "00", "");
                시장가 매수 - openApi.SendOrder("RQ_1", "0101", "5015123410", 1, "000660", 10, 0, "03", "");
                매수 정정 - openApi.SendOrder("RQ_1","0101", "5015123410", 5, "000660", 10, 49500, "00", "1");
                매수 취소 - openApi.SendOrder("RQ_1", "0101", "5015123410", 3, "000660", 10, 0, "00", "2");
        """
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rq_name, screen_no, account_no, order_type, code, qty, price, hoga_gb, org_order_no])

    def set_input_value(self, input_id, input_value):
        """
        원형 : void SetInputValue(BSTR sID, BSTR sValue)
        설명 : Tran 입력 값을 서버통신 전에 입력한다.
        입력값 :
            sID – 아이템명
            sValue – 입력 값
        반환값 : 없음
        비고 :
            Ex) openApi.SetInputValue("종목코드", "000660");
                openApi.SetInputValue("계좌번호", "5015123401");
        """
        self.dynamicCall("SetInputValue(QString, QString)", input_id, input_value)

    @SyncRequestDecorator.sync_request
    def disconnect_real_data(self, screen_no):
        """
        원형 : void DisconnectRealData(LPCTSTR sScnNo)
        설명 : 화면 내 모든 리얼데이터 요청을 제거한다.
        입력값 : sScnNo – 화면번호[4]
        반환값 : 없음
        비고 :
            화면을 종료할 때 반드시 위 함수를 호출해야 한다.
            Ex) openApi.DisconnectRealData("0101");
        """
        self.dynamicCall("DisconnectRealData(QString)", screen_no)

    def comm_rq_data(self, rq_name, tr_code, prev_next, screen_no):
        """
        원형 : LONG CommRqData(BSTR sRQName, BSTR sTrCode, long nPrevNext, BSTR sScreenNo)
        설명 : Tran을 서버로 송신한다.
        입력값 :
            BSTR sRQName
            BSTR sTrCode
            long nPrevNext
            BSTR sScreenNo
        반환값
            OP_ERR_SISE_OVERFLOW - 과도한 시세조회로 인한 통신불가
            OP_ERR_RQ_STRUCT_FAIL - 입력 구조체 생성 실패
            OP_ERR_RQ_STRING_FAIL - 요청전문 작성 실패
            OP_ERR_NONE - 정상처리
        비고
            sRQName – 사용자구분 명
            sTrCode - Tran명 입력
            nPrevNext - 0:조회, 2:연속
            sScreenNo - 4자리의 화면번호
            Ex) openApi.CommRqData( "RQ_1", "OPT00001", 0, "0101");
        """
        self.response_comm_rq_data = self.dynamicCall("CommRqData(QString, QString, int, QString",
                                                      rq_name, tr_code, prev_next, screen_no)
        if self.response_comm_rq_data == KWErrorCode.OP_ERR_NONE:
            pass
        else:
            print('알 수 없는 오류 : %s' % str(self.response_comm_rq_data))

    @SyncRequestDecorator.sync_callback
    def on_receive_msg(self, screen_no, rq_name, tr_code, msg):
        """
        원형 : void OnReceiveMsg(LPCTSTR sScrNo, LPCTSTR sRQName, LPCTSTR sTrCode, LPCTSTR sMsg)
        설명 : 서버통신 후 메시지를 받은 시점을 알려준다.
        입력값 :
            sScrNo – 화면번호
            sRQName – 사용자구분 명
            sTrCode – Tran 명
            sMsg – 서버메시지
        반환값 : 없음
        비고 :
            sScrNo – CommRqData의 sScrNo와 매핑된다.
            sRQName – CommRqData의 sRQName 와 매핑된다.
            sTrCode – CommRqData의 sTrCode 와 매핑된다.
        """
        self.logger.debug("on_receive_msg : %s %s %s %s" % (screen_no, rq_name, tr_code, msg))
        # print("on_receive_msg : %s %s %s %s" % (screen_no, rq_name, tr_code, msg))

    @SyncRequestDecorator.sync_callback
    def on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next,
                           data_length, error_code, message, sp_im_msg):
        """
        원형 : void OnReceiveTrData(LPCTSTR sScrNo, LPCTSTR sRQName, LPCTSTR sTrCode, LPCTSTR sRecordName,
        LPCTSTR sPreNext, LONG nDataLength, LPCTSTR sErrorCode, LPCTSTR sMessage, LPCTSTR sSplmMsg)
        설명 : 서버통신 후 데이터를 받은 시점을 알려준다.
        입력값 :
            sScrNo – 화면번호
            sRQName – 사용자구분 명
            sTrCode – Tran 명
            sRecordName – Record 명
            sPreNext – 연속조회 유무
            nDataLength – 1.0.0.1 버전 이후 사용하지 않음.
            sErrorCode – 1.0.0.1 버전 이후 사용하지 않음.
            sMessage – 1.0.0.1 버전 이후 사용하지 않음.
            sSplmMsg - 1.0.0.1 버전 이후 사용하지 않음.
        반환값 : 없음
        비고 :
            sRQName – CommRqData의 sRQName과 매핑되는 이름이다.
            sTrCode – CommRqData의 sTrCode과 매핑되는 이름이다.
        """

        if tr_code == 'KOA_NORMAL_BUY_KP_ORD':
            print('구매 콜백')
            return

        try:
            assert (KWErrorCode.OP_ERR_NONE == self.response_comm_rq_data)
            assert (tr_code in self.tr_list)

            self.logger.info("tr_code : %s, rq_name : %s" % (tr_code, rq_name))

            tr_option = self.tr_list[tr_code]

            if hasattr(tr_option, 'record_name'):
                repeat_cnt = self.get_repeat_cnt(tr_code, tr_option.record_name)

            if hasattr(tr_option, 'record_name_single'):
                repeat_cnt_single = self.get_repeat_cnt(tr_code, tr_option.record_name_single)

            if hasattr(tr_option, 'record_name_multiple'):
                repeat_cnt_multiple = self.get_repeat_cnt(tr_code, tr_option.record_name_multiple)

            comm_data = {}
            if tr_code == 'opw00001':
                prev_next = '0'

            if not prev_next:
                if tr_code == 'opt10023':
                    print('데이타 없음.')
                    return
                print("comm_data Error")

            elif int(prev_next) == 0:
                # TODO : 싱글 데이터 수집할 때, 전체 index 수집
                # 싱글 데이터 수집
                if tr_option.record_name_single:
                    comm_data['single'] = tr_option.tr_opt_data(tr_code, rq_name, 0)
                    self.logger.debug(comm_data['single'])
                # 멀티 데이터 수집
                if tr_option.record_name_multiple:
                    comm_data['multiple'] = tr_option.tr_opt_data_ex(tr_code, rq_name)
                    self.logger.debug(comm_data['multiple'])

            elif int(prev_next) == 2:
                # TODO : 싱글 데이터 수집할 때, 전체 index 수집
                # TODO : 전체 멀티 데이터 수집을 위해 comm_rq_data 재요청 및 재수집
                # 싱글 데이터 수집
                if tr_option.record_name_single:
                    comm_data['single'] = tr_option.tr_opt_data(tr_code, rq_name, 0)
                    self.logger.debug(comm_data['single'])
                # 멀티 데이터 수집
                if tr_option.record_name_multiple:
                    comm_data['multiple'] = tr_option.tr_opt_data_ex(tr_code, rq_name)
                    self.logger.debug(comm_data['multiple'])

            else:
                assert (int(prev_next) == 0 or int(prev_next) == 2)

            # 데이터 종합
            if tr_code not in self.receive_tr_data_handler:
                self.receive_tr_data_handler[tr_code] = {}

            if screen_no not in self.receive_tr_data_handler[tr_code]:
                self.receive_tr_data_handler[tr_code][screen_no] = {}

            self.receive_tr_data_handler[tr_code][screen_no] = {
                "response": self.response_comm_rq_data,
                "rq_name": rq_name,
                "tr_code": tr_code,
                "record_name": record_name,
                "pre_next": prev_next,
                "comm_data": comm_data
            }

            self.processData(self.receive_tr_data_handler[tr_code][screen_no])

        except Exception as e:
            print("\n")
            print("\t\t\t", "###########################################")
            print("\t\t\t", e)
            print("\t\t\t", "###########################################")
            print("\n")

        self.disconnect_real_data(screen_no)

        print('on_receive_tr_data finished')

    def processData(self, commData):
        if commData['tr_code'] == 'opw00001':
            # 예수금상세현황요청
            res = get_data_from_single_comm_data(commData, ['주문가능금액'])
            self.available_price = float(res['주문가능금액'])
            self.logger.info('주문가능금액 : %.1f' % self.available_price)
        elif commData['tr_code'] == 'opt10023':
            # 거래량급증요청
            idx_stock_code = None
            idx_stock_name = None
            for idx, header in enumerate(commData['comm_data']['multiple']['header']):
                if header == '종목코드':
                    idx_stock_code = idx
                elif header == '종목명':
                    idx_stock_name = idx

                if idx_stock_code is not None and idx_stock_name is not None:
                    break

            stock_list = []
            for row in commData['comm_data']['multiple']['rows']:
                stock_list.append(row[idx_stock_code])
                self.logger.debug('종목명(종목코드) : %s(%s)' % (row[idx_stock_name], row[idx_stock_code]))

            self.stock_list = stock_list
            self.logger.info('종목수 : %i' % len(self.stock_list))
        elif commData['tr_code'] == 'opt10001':
            # 주식기본정보요청
            # while database.DB_LOCKED:
            #     sleep(0.1)
            # database.DB_LOCKED = True
            database.db_lock.acquire()
            print('database.db_lock.acquire() 11')
            session = Session()
            res = get_data_from_single_comm_data(commData, ['종목코드', '종목명'])
            item = session.query(StockBasicInfo).filter(StockBasicInfo.종목코드 == res['종목코드']).first()
            obj = StockBasicInfo(res['종목코드'], res['종목명'])
            if item is None:
                session.add(obj)
            else:
                item.종목명 = res['종목명']
                item.lastupdate = datetime.now()
            session.commit()
            Session.remove()
            # database.DB_LOCKED = False
            database.db_lock.release()
            print('database.db_lock.release() 11')
        elif commData['tr_code'] == 'opt10081':
            # 주식일봉차트조회요청
            res = get_data_from_single_comm_data(commData, ['종목코드'])
            stock_code = res['종목코드']

            print('종목코드 start : %s' % stock_code)
            res = get_data_from_multiple_comm_data(commData, ['현재가', '거래량', '거래대금', '일자', '시가', '고가', '저가', '전일종가'])
            # while database.DB_LOCKED:
            #     sleep(0.1)
            # database.DB_LOCKED = True
            database.db_lock.acquire()
            print('database.db_lock.acquire() 22')
            session = Session()
            for idx, obj in enumerate(res):
                obj = StockDayCandleChart(stock_code, float(obj['현재가']), float(obj['거래량']), float(obj['거래대금']),
                                          obj['일자'], float(obj['시가']), float(obj['고가']), float(obj['저가']))
                item = session.query(StockDayCandleChart) \
                    .filter(StockDayCandleChart.종목코드 == stock_code) \
                    .filter(StockDayCandleChart.일자 == obj.일자) \
                    .first()
                if item is None:
                    session.add(obj)
                else:
                    if idx == 0:
                        # 첫 라인이 업데이트면 신규 데이타 없음
                        item.lastupdate = datetime.now()
                        break
                    continue
            session.commit()
            Session.remove()
            # database.DB_LOCKED = False
            database.db_lock.release()
            print('database.db_lock.release() 22')
            print('종목코드 end : %s' % stock_code)
        else:
            print(commData)

        print('processData finished')

    @SyncRequestDecorator.sync_callback
    def on_receive_real_data(self, jongmok_code, real_type, real_data):
        """
        원형 : void OnReceiveRealData(LPCTSTR sJongmokCode, LPCTSTR sRealType, LPCTSTR sRealData)
        설명 : 실시간데이터를 받은 시점을 알려준다.
        입력값 :
            sJongmokCode – 종목코드
            sRealType – 리얼타입
            sRealData – 실시간 데이터전문
        반환값 : 없음
        """
        if "주식호가잔량" == real_type:
            print("on_receive_real_data 1: %s %s %s" % (jongmok_code, real_type, real_data))
        elif "주식체결" == real_type:
            # print("on_receive_real_data 2: %s %s %s" % (jongmok_code, real_type, real_data))
            pass
        elif "종목프로그램매매" == real_type:
            print("on_receive_real_data 3: %s %s %s" % (jongmok_code, real_type, real_data))
        elif "주식우선호가" == real_type:
            print("on_receive_real_data 4: %s %s %s" % (jongmok_code, real_type, real_data))
        elif "ECN주식체결" == real_type:
            # print("on_receive_real_data 5: %s %s %s" % (jongmok_code, real_type, real_data))
            pass
        elif "주식시세" == real_type:
            # print("on_receive_real_data 6: %s %s %s" % (jongmok_code, real_type, real_data))
            pass
        elif "주식당일거래원" == real_type:
            # print("on_receive_real_data 7: %s %s %s" % (jongmok_code, real_type, real_data))
            pass
        elif "ECN주식시세" == real_type:
            # print("on_receive_real_data 8: %s %s %s" % (jongmok_code, real_type, real_data))
            pass
        else:
            print("on_receive_real_data 9: %s %s %s" % (jongmok_code, real_type, real_data))

    @SyncRequestDecorator.sync_callback
    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """
        원형 : void OnReceiveChejanData(LPCTSTR sGubun, LONG nItemCnt, LPCTSTR sFidList);
        설명 : 체결데이터를 받은 시점을 알려준다.
        입력값 :
            sGubun – 체결구분
            nItemCnt - 아이템갯수
            sFidList – 데이터리스트
        반환값 : 없음
        비고 :
            sGubun – 0:주문체결통보, 1:잔고통보, 3:특이신호
            sFidList – 데이터 구분은 ';' 이다.
        """
        print("on_receive_chejan_data")

    @SyncRequestDecorator.sync_callback
    def on_receive_condition(self, code, type, condition_name, condition_index):
        """
        원형 : void OnReceiveRealCondition(LPCTSTR strCode, LPCTSTR strType, LPCTSTR strConditionName, LPCTSTR strConditionIndex)
        설명 : 조건검색 실시간 편입,이탈 종목을 받을 시점을 알려준다.
        입력값 :
            LPCTSTR strCode : 종목코드
            LPCTSTR strType : 편입("I"), 이탈("D")
            LPCTSTR strConditionName : 조건명
            LPCTSTR strConditionIndex : 조건명 인덱스
        반환값 : 없음
        비고 :
            strConditionName에 해당하는 종목이 실시간으로 들어옴.
            strType으로 편입된 종목인지 이탈된 종목인지 구분한다.
        """
        print("on_receive_condition")

    @SyncRequestDecorator.sync_callback
    def on_receive_tr_condition(self, screen_no, code_list, condition_name, index, next):
        """
        원형 : void OnReceiveTrCondition(LPCTSTR sScrNo, LPCTSTR strCodeList, LPCTSTR strConditionName, int nIndex, int nNext)
        설명 : 조건검색 조회응답으로 종목리스트를 구분자(";")로 붙어서 받는 시점.
        입력값 :
            LPCTSTR sScrNo : 종목코드
            LPCTSTR strCodeList : 종목리스트(";"로 구분)
            LPCTSTR strConditionName : 조건명
            int nIndex : 조건명 인덱스
            int nNext : 연속조회(2:연속조회, 0:연속조회없음)
        반환값 : 없음
        """
        print("on_receive_tr_condition")

    @SyncRequestDecorator.sync_callback
    def on_receive_condition_ver(self, ret, msg):
        """
        원형 : void OnReceiveConditionVer(long lRet, LPCTSTR sMsg)
        설명 : 로컬에 사용자 조건식 저장 성공 여부를 확인하는 시점
        입력값 : long lRet - 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
        반환값 : 없음
        """
        print("on_receive_condition_ver")

    def get_repeat_cnt(self, tr_code, record_name):
        """
        원형 : LONG GetRepeatCnt(LPCTSTR sTrCode, LPCTSTR sRecordName)
        설명 : 레코드 반복횟수를 반환한다.
        입력값 :
            sTrCode – Tran 명
            sRecordName – 레코드 명
        반환값 : 레코드의 반복횟수
        비고 : Ex) openApi.GetRepeatCnt("OPT00001", "주식기본정보");
        """
        return self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, record_name)

    def get_comm_data_ex(self, tr_code, rq_name):
        """
        원형 : VARIANT GetCommDataEx(LPCTSTR strTrCode, LPCTSTR strRecordName)
        설명 : 차트 조회 데이터를 배열로 받아온다.
        입력값 :
            LPCTSTR strTrCode : 조회한TR코드
            LPCTSTR strRecordName: 조회한 TR명
        비고 :
            조회 데이터가 많은 차트 경우 GetCommData()로 항목당 하나씩 받아오는 것 보다 한번에 데이터 전부를 받아서 사용자가 처리할 수 있도록 배열로 받는다.
        """
        return self.dynamicCall("GetCommDataEx(QString, QString)", tr_code, rq_name)

    def get_comm_data(self, tr_code, record_name, index, item_name):
        """
        원형 : BSTR GetCommData(LPCTSTR strTrCode, LPCTSTR strRecordName, long nIndex, LPCTSTR strItemName)
        설명 : 수신 데이터를 반환한다.
        입력값 :
            strTrCode – Tran 코드
            strRecordName – 레코드명
            nIndex – 복수데이터 인덱스
            strItemName – 아이템명
        반환값 : 수신 데이터
        비고 : Ex)현재가출력 - openApi.GetCommData("OPT00001", "주식기본정보", 0, "현재가");
        """
        return self.dynamicCall("GetCommData(QString, QString, int, QString)",
                                tr_code, record_name, index, item_name).strip()
