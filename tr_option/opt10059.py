from tr_option.base import KWTR
from copy import deepcopy


# [ opt10059 : 종목별투자자기관별요청 ]
class Opt10059(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opt10059'
        self.rq_name = '종목별투자자기관별요청'

        self.record_name_multiple = '종목별투자자기관별'
        self.header_multiple = [
            '일자', '현재가', '대비기호', '전일대비', '등락율', '누적거래량', '누적거래대금', '개인투자자', '외국인투자자', '기관계', '금융투자', '보험', '투신', '기타금융',
            '은행', '연기금등', '사모펀드', '국가', '기타법인', '내외국인',
        ]

    def tr_opt(self, date, code, input2, input3, input4, prev_next, screen_no):
        # 일자 = YYYYMMDD (20160101 연도4자리, 월 2자리, 일 2자리 형식)
        # 종목코드 = 전문 조회할 종목코드
        # 금액수량구분 = 1:금액, 2:수량
        # 매매구분 = 0:순매수, 1:매수, 2:매도
        # 단위구분 = 1000:천주, 1:단주

        self.core.set_input_value('일자', date)
        self.core.set_input_value('종목코드', code)
        self.core.set_input_value('금액수량구분', input2)
        self.core.set_input_value('매매구분', input3)
        self.core.set_input_value('단위구분', input4)
        return self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)
