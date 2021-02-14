#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util


class StockMonitor:
    def __init__(self, __mainLogger, __sysTrader, __SCREEN_NUMBER):
        """
        자동투자시스템 주식 매니저
        """
        self.sysTrader = __sysTrader
        self.logger = __mainLogger

        self.SCREEN_NUMBER = __SCREEN_NUMBER

        self.result = {}
        self.params = {}

    def requestBasicStockInfo(self, strCode):
        """주식 기본정보 요청
        :param strCode:
        :return:
        """
        self.sysTrader.kiwoom_SetInputValue("종목코드", strCode)
        res = self.sysTrader.kiwoom_CommRqData("주식기본정보", "OPT10001", 0, self.SCREEN_NUMBER)
        return res

    def processStockBasicInfo(self, sTRCode, sRQName):
        list_item_name = ["종목명", "현재가", "등락율", "거래량", "시가", "고가", "저가",
                          "액면가", "시가총액", "대비기호", "신용비율", "250최고", "250최저"]

        stock_code = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, "종목코드")
        stock_code = stock_code.strip()

        dict_stock = {}
        for item_name in list_item_name:
            item_value = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, item_name)
            item_value = item_value.strip()
            dict_stock[item_name] = item_value

        self.logger.debug("주식기본정보: %s, %s" % (stock_code, dict_stock))

    def requestBuyGigwan(self, strCode, refDate):
        """종목별투자자
        :param strCode: 종목코드
        :param refDate: Reference date. In format of yyyyMMdd : 기준일자
        :return:
        """
        self.sysTrader.kiwoom_SetInputValue("일자", refDate)
        self.sysTrader.kiwoom_SetInputValue("종목코드", strCode)
        self.sysTrader.kiwoom_SetInputValue("금액수량구분", str(1))
        self.sysTrader.kiwoom_SetInputValue("매매구분", str(0))
        self.sysTrader.kiwoom_SetInputValue("단위구분", str(1000))
        res = self.sysTrader.kiwoom_CommRqData("종목별투자자", "opt10059", "0", self.SCREEN_NUMBER)
        return res

    def processBuyGigwan(self, sTRCode, sRQName):
        list_item_name = ["일자", "현재가", "대비기호", "전일대비", "등락율", "누적거래량", "누적거래대금",
                          "개인투자자", "외국인투자자", "기관계"]

        dict_stock = {}
        for item_name in list_item_name:
            item_value = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, item_name)
            item_value = item_value.strip()
            dict_stock[item_name] = item_value

        self.logger.debug("주식투자자정보: %s" % dict_stock)

    def requestMinuteCandleChart(self, strCode, tick=1, fix=1, size=240, nPrevNext=0):
        """주식분봉차트조회
        :param strCode: 종목코드
        :param tick: 틱범위 (1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분)
        :param fix: 수정주가구분 (0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
        :param size: Fetch these many candle sticks.
        :param nPrevNext:
        :return:
        """
        self.params['size'] = size
        self.sysTrader.kiwoom_SetInputValue("종목코드", strCode)
        self.sysTrader.kiwoom_SetInputValue("틱범위", str(tick))
        self.sysTrader.kiwoom_SetInputValue("수정주가구분", str(fix))
        res = self.sysTrader.kiwoom_CommRqData("주식분봉차트조회", "opt10080", nPrevNext, self.SCREEN_NUMBER)
        return res

    def processMinuteCandleChart(self, sRQName, sTRCode, sPreNext):
        cnt = self.sysTrader.kiwoom_GetRepeatCnt(sTRCode, sRQName)

        stock_code = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, "종목코드")
        stock_code = stock_code.strip()

        done = False  # 파라미터 처리 플래그
        # result = self.result.get('result', [])
        result = []
        cnt_acc = len(result)

        list_item_name = []
        # list_item_name = ["현재가", "거래량", "체결시간", "시가", "고가",
        #                   "저가", "수정주가구분", "수정비율", "대업종구분", "소업종구분",
        #                   "종목정보", "수정주가이벤트", "전일종가"]
        list_item_name = ["체결시간", "시가", "고가", "저가", "현재가", "거래량"]

        for nIdx in range(cnt):
            item = {'종목코드': stock_code}
            for item_name in list_item_name:
                item_value = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name)
                item_value = item_value.strip()
                item[item_name] = item_value

            # 범위조회 파라미터
            date_from = int(self.params.get("date_from", "000000000000"))
            date_to = int(self.params.get("date_to", "999999999999"))

            # 결과는 최근 데이터에서 오래된 데이터 순서로 정렬되어 있음
            date = None
            date = int(item["체결시간"])

            # 개수 파라미터처리
            if cnt_acc + nIdx >= self.params.get('size', float("inf")):
                done = True
                break

            result.append(util.convert_kv(item))

        # 차트 업데이트
        self.result['result'] = result

        if not done and cnt > 0 and sPreNext == '2':
            self.result['nPrevNext'] = 2
            self.result['done'] = False
        else:
            # 연속조회 완료
            self.logger.debug("차트 연속조회 완료")
            self.result['nPrevNext'] = 0
            self.result['done'] = True

        for item in self.result['result']:
            print(" time : %s, open : %f, high : %f, low : %f, 현재가 : %s, volume : %f"
                  % (item['time'], item['open'], item['high'], item['low'], item['현재가'], item['volume']))

    def requestDayCandleChart(self, strCode, tick, fix, size, nPrevNext):
        """
        주식일봉차트조회
        :param strCode: 종목코드
        :param tick: 틱범위
        :param fix: 수정주가구분 (0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락)
        :param size: Fetch these many candle sticks.
        :param nPrevNext:
        :return:
        """
        self.params['size'] = size
        self.sysTrader.kiwoom_SetInputValue("종목코드", strCode)
        self.sysTrader.kiwoom_SetInputValue("틱범위", str(tick))
        self.sysTrader.kiwoom_SetInputValue("수정주가구분", str(fix))
        res = self.sysTrader.kiwoom_CommRqData("주식일봉차트조회", "opt10081", nPrevNext, self.SCREEN_NUMBER)
        return res

    def processDayCandleChart(self, sRQName, sTRCode, sPreNext):
        cnt = self.sysTrader.kiwoom_GetRepeatCnt(sTRCode, sRQName)

        stock_code = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, 0, "종목코드")
        stock_code = stock_code.strip()

        done = False  # 파라미터 처리 플래그
        # result = self.result.get('result', [])
        result = []
        cnt_acc = len(result)

        list_item_name = ["일자", "시가", "고가", "저가", "현재가", "거래량"]

        for nIdx in range(cnt):
            item = {'종목코드': stock_code}
            for item_name in list_item_name:
                item_value = self.sysTrader.kiwoom_GetCommData(sTRCode, sRQName, nIdx, item_name)
                item_value = item_value.strip()
                item[item_name] = item_value

            # 범위조회 파라미터
            date_from = int(self.params.get("date_from", "000000000000"))
            date_to = int(self.params.get("date_to", "999999999999"))

            # 결과는 최근 데이터에서 오래된 데이터 순서로 정렬되어 있음
            date = None
            date = int(item["일자"])
            if date > date_to:
                continue
            elif date < date_from:
                done = True
                break

            # 개수 파라미터처리
            if cnt_acc + nIdx >= self.params.get('size', float("inf")):
                done = True
                break

            result.append(util.convert_kv(item))

        # 차트 업데이트
        self.result['result'] = result
        self.logger.debug(result)

        if not done and cnt > 0 and sPreNext == '2':
            self.result['nPrevNext'] = 2
            self.result['done'] = False
        else:
            # 연속조회 완료
            self.logger.debug("차트 연속조회 완료")
            self.result['nPrevNext'] = 0
            self.result['done'] = True

        for item in self.result['result']:
            print(" date : %s, open : %f, high : %f, low : %f, 현재가 : %s, volume : %f"
                  % (item['date'], item['open'], item['high'], item['low'], item['현재가'], item['volume']))

    def requestConditionList(self):
        """
        조건검색 목록요청
        :return:
        """
        lRet = self.sysTrader.kiwoom.dynamicCall("GetConditionLoad()")
        return lRet

    def processConditionList(self, lRet, sMsg):
        """
        조건검색 조건목록 결과수신
        GetConditionNameList() 실행하여 조건목록 획득.
        첫번째 조건 이용하여 [조건검색]SendCondition() 실행
        :param lRet:
        :return:
        """
        self.logger.debug(sMsg)
        if lRet:
            # 001^거래량급등;000^일목균형;002^음운 진입;
            sRet = self.sysTrader.kiwoom.dynamicCall("GetConditionNameList()")
            pairs = [idx_name.split('^') for idx_name in [cond for cond in sRet.split(';')]]
            if len(pairs) > 0:
                for pair in pairs:
                    if pair[0] != '':
                        nIndex = int(pair[0])
                        strConditionName = pair[1]
                        if strConditionName == '거래량급등':
                            # self.sysTrader.kiwoom_SendCondition(strConditionName, nIndex)
                            self.realtimeSendCondition(strConditionName, nIndex)

    def realtimeSendCondition(self, strConditionName, nIndex):
        """
        조검검색 실시간 요청. OnReceiveConditionVer() 안에서 호출해야 함.
        실시간 요청이라도 OnReceiveTrCondition() 콜백 먼저 호출됨.
        조검검색 결과 변경시 OnReceiveRealCondition() 콜백 호출됨.
          SendCondition(
          BSTR strScrNo,            // 화면번호
          BSTR strConditionName,    // 조건식 이름
          int nIndex,               // 조건명 인덱스
          int nSearch               // 조회구분, 0:조건검색, 1:실시간 조건검색
          )
        :param strConditionName: 조건식 이름
        :param nIndex: 조건명 인덱스
        :return: 1: 성공, 0: 실패
        """
        self.logger.debug("조건검색 실시간 요청 : %s" % strConditionName)

        lRet = self.sysTrader.kiwoom.dynamicCall(
            "SendCondition(QString, QString, int, int)",
            [self.SCREEN_NUMBER, strConditionName, nIndex, 1]
        )
        return lRet

    def processConditionListChange(self, strCodeList):
        """
        조건검색 결과 수신
          OnReceiveTrCondition(
          BSTR sScrNo,              // 화면번호
          BSTR strCodeList,         // 종목코드 리스트
          BSTR strConditionName,    // 조건식 이름
          int nIndex,               // 조건명 인덱스
          int nNext                 // 연속조회 여부
          )
        :param strCodeList: 종목코드 리스트
        :return:
        """
        list_str_code = list(filter(None, strCodeList.split(';')))
        self.logger.debug("조건검색 결과: %s" % (list_str_code,))

        # # 조검검색 결과를 종목 모니터링 리스트에 추가
        # logger.debug("1111111111")
        # self.kiwoom.set_stock2monitor.add(set(list_str_code))
        # # print(self.kiwoom.set_stock2monitor)
        # # self.kiwoom.set_stock2monitor.update(set(list_str_code))
        # logger.debug("222222")
