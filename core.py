#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

from constants import KWErrorCode


class KWCore(QAxWidget):

    tr_list = {}

    def __init__(self):
        super().__init__()
        assert(self.setControl("KHOPENAPI.KHOpenAPICtrl.1"))
        self._init_connect_events()

    def _init_connect_events(self):
        # 서버 접속 관련 이벤트
        self.response_connect_status = None
        self.loop_event_connect = QEventLoop()
        self.OnEventConnect.connect(self.on_event_connect)

        # 서버통신 후 데이터를 받은 시점을 알려준다.
        self.response_comm_rq_data = None
        self.receive_tr_data_handler = {}
        self.loop_receive_tr_data = QEventLoop()
        self.OnReceiveTrData.connect(self.on_receive_tr_data)

        # 실시간데이터를 받은 시점을 알려준다.
        self.loop_receive_real_data = QEventLoop()
        self.OnReceiveRealData.connect(self.on_receive_real_data)

        # 서버통신 후 메시지를 받은 시점을 알려준다.
        self.loop_receive_msg = QEventLoop()
        self.OnReceiveMsg.connect(self.on_receive_msg)

        # 체결데이터를 받은 시점을 알려준다.
        self.loop_receive_chejan_data = QEventLoop()
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)

        # 조건검색 실시간 편입,이탈 종목을 받을 시점을 알려준다.
        self.loop_receive_condition = QEventLoop()
        self.OnReceiveRealCondition.connect(self.on_receive_condition)

        # 조건검색 조회응답으로 종목리스트를 구분자(";")로 붙어서 받는 시점.
        self.loop_receive_tr_condition = QEventLoop()
        self.OnReceiveTrCondition.connect(self.on_receive_tr_condition)

        # 로컬에 사용자 조건식 저장 성공 여부를 확인하는 시점
        self.loop_receive_condition_ver = QEventLoop()
        self.OnReceiveConditionVer.connect(self.on_receive_condition_ver)

    def comm_connect(self):
        """
        원형 : LONG CommConnect()
        설명 : 로그인 윈도우 실행
        반환값 : 0 - 성공, 음수값은 실패
        비고 : 로그인이 성공하거나 실패하는 경우 OnEventConnect 이벤트가 발생하고 이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.
        """
        self.dynamicCall("CommConnect()")
        self.loop_event_connect.exec_()

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
        print("on_event_connect")

        self.response_connect_status = int(err_code)

        if err_code == KWErrorCode.OP_ERR_NONE:
            print("연결 성공")
        else:
            print("연결 실패")

        if self.loop_event_connect.isRunning():
            self.loop_event_connect.exit()

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

    def set_input_value(self, id, value):
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
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

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
        self.response_comm_rq_data = self.dynamicCall("CommRqData(QString, QString, int, QString", rq_name, tr_code, prev_next, screen_no)
        self.loop_receive_tr_data.exec_()

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
        print("on_receive_msg")
        print(msg)

        print("~*~ Ended OnReceiveMsg event! ~*~")
        if self.loop_receive_msg.isRunning():
            self.loop_receive_msg.exit()

    def on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next, data_length, error_code, message,
                           sp_im_msg):
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
        print(screen_no)
        print(rq_name)
        print(tr_code)
        print(record_name)
        print(prev_next)
        try:
            assert (self.response_connect_status == KWErrorCode.OP_ERR_NONE)
            assert (KWErrorCode.OP_ERR_NONE == self.response_comm_rq_data)
            assert (tr_code in self.tr_list)

            print("~*~ Called OnReceiveTrData event! ~*~")

            print("[ INFO ]")
            print("\t screen_no :", screen_no)
            print("\t rq_name :", rq_name)
            print("\t tr_code :", tr_code)
            print("\t record_name :", record_name)
            print("\t prev_next: ", prev_next)
            print("\n")
            print("[ comm_rq_data ]")
            print("\t response_comm_rq_data :", self.response_comm_rq_data)

            tr_option = self.tr_list[tr_code]

            if hasattr(tr_option, 'record_name'):
                repeat_cnt = self.get_repeat_cnt(tr_code, tr_option.record_name)
                print("\t get_repeat_cnt(record_name) :", repeat_cnt)

            if hasattr(tr_option, 'record_name_single'):
                repeat_cnt_single = self.get_repeat_cnt(tr_code, tr_option.record_name_single)
                print("\t get_repeat_cnt(record_name_single) :", repeat_cnt_single)

            if hasattr(tr_option, 'record_name_multiple'):
                repeat_cnt_multiple = self.get_repeat_cnt(tr_code, tr_option.record_name_multiple)
                print("\t get_repeat_cnt(record_name_multiple) :", repeat_cnt_multiple)

            comm_data = {}

            if not prev_next:
                print("comm_data Error")

            elif int(prev_next) == 0:
                # TODO : 싱글 데이터 수집할 때, 전체 index 수집
                # 싱글 데이터 수집
                if tr_option.record_name_single:
                    comm_data['single'] = tr_option.tr_opt_data(tr_code, rq_name, 0)
                # 멀티 데이터 수집
                if tr_option.record_name_multiple:
                    comm_data['multiple'] = tr_option.tr_opt_data_ex(tr_code, rq_name)

            elif int(prev_next) == 2:
                # TODO : 싱글 데이터 수집할 때, 전체 index 수집
                # TODO : 전체 멀티 데이터 수집을 위해 comm_rq_data 재요청 및 재수집
                # 싱글 데이터 수집
                if tr_option.record_name_single:
                    comm_data['single'] = tr_option.tr_opt_data(tr_code, rq_name, 0)
                # 멀티 데이터 수집
                if tr_option.record_name_multiple:
                    comm_data['multiple'] = tr_option.tr_opt_data_ex(tr_code, rq_name)

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

        except Exception as e:
            print("\n")
            print("\t\t\t", "###########################################")
            print("\t\t\t", e)
            print("\t\t\t", "###########################################")
            print("\n")

        finally:
            print("~*~ Ended OnReceiveTrData event! ~*~")
            if self.loop_receive_tr_data.isRunning():
                self.loop_receive_tr_data.exit()

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
        print("Called OnReceiveRealData", jongmok_code, real_type, real_data)

        if self.loop_receive_real_data.isRunning():
            self.loop_receive_real_data.exit()
            print("Ended OnReceiveRealData")
            assert (False)

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
        assert(False)

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
        assert (False)

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
        assert (False)

    def on_receive_condition_ver(self, ret, msg):
        """
        원형 : void OnReceiveConditionVer(long lRet, LPCTSTR sMsg)
        설명 : 로컬에 사용자 조건식 저장 성공 여부를 확인하는 시점
        입력값 : long lRet - 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
        반환값 : 없음
        """
        print("on_receive_condition_ver")
        assert (False)

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
        return self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, record_name, index,
                                item_name).strip()