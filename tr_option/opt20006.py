from tr_option.base import KWTR
from copy import deepcopy


# [ opt20006 : 업종일봉조회요청 ]
class Opt20006(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opt20006'
        self.rq_name = '업종일봉조회요청'

        self.record_name_single = '업종일봉차트'
        self.header_single = [
            '업종코드',
        ]

        self.record_name_multiple = '업종일봉조회'
        self.header_multiple = [
            '현재가', '거래량', '일자', '시가', '고가', '저가', '거래대금', '대업종구분', '소업종구분', '종목정보', '전일종가',
        ]

    def tr_opt(self, input0, input1, prev_next, screen_no):
        # 업종코드 = 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고
        # 기준일자 = YYYYMMDD (20160101 연도4자리, 월 2자리, 일 2자리 형식)

        self.core.set_input_value('업종코드', input0)
        self.core.set_input_value('기준일자', input1)
        self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)

        self.tr_data = deepcopy(self.core.receive_tr_data_handler[self.tr_code][screen_no])

        return self.tr_data
