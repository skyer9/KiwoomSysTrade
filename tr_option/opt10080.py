from tr_option.base import KWTR
from copy import deepcopy


# [ opt10080 : 주식분봉차트조회요청 ]
class Opt10080(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opt10080'
        self.rq_name = '주식분봉차트조회요청'

        self.record_name_single = '주식분차트'
        self.header_single = [
            '종목코드',
        ]

        self.record_name_multiple = '주식분봉차트조회'
        self.header_multiple = [
            '현재가', '거래량', '체결시간', '시가', '고가', '저가', '수정주가구분', '수정비율', '대업종구분', '소업종구분', '종목정보', '수정주가이벤트', '전일종가',
        ]

    def tr_opt(self, code, tick_range, fix, prev_next, screen_no):
        # 종목코드 = 전문 조회할 종목코드
        # 틱범위 = 1:1분, 3:3분, 5:5분, 10:10분, 15:15분, 30:30분, 45:45분, 60:60분
        # 수정주가구분 = 0 or 1, 수신데이터 1:유상증자, 2:무상증자, 4:배당락, 8:액면분할, 16:액면병합, 32:기업합병, 64:감자, 256:권리락

        self.core.set_input_value('종목코드', code)
        self.core.set_input_value('틱범위', tick_range)
        self.core.set_input_value('수정주가구분', fix)
        return self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)
