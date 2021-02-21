from tr_option.base import KWTR
from copy import deepcopy


# [ opt10023 : 거래량급증요청 ]
class Opt10023(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opt10023'
        self.rq_name = '거래량급증요청'

        self.record_name_multiple = '거래량급증'
        self.header_multiple = [
            '종목코드', '종목명', '현재가', '전일대비기호', '전일대비', '등락률', '이전거래량', '현재거래량', '급증량', '급증률',
        ]

    def tr_opt(self, market_type, sort_type, time_type, trade_type, minutes,
               jongmok_type, price_type, prev_next, screen_no):
        # 시장구분 = 000:전체, 001:코스피, 101:코스닥
        # 정렬구분 = 1:급증량, 2:급증률
        # 시간구분 = 1:분, 2:전일
        # 거래량구분 = 5:5천주이상, 10:만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
        # 시간 = 분 입력
        # 종목조건 = 0:전체조회, 1:관리종목제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기
        # 가격구분 = 0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상

        self.core.set_input_value('시장구분', market_type)
        self.core.set_input_value('정렬구분', sort_type)
        self.core.set_input_value('시간구분', time_type)
        self.core.set_input_value('거래량구분', trade_type)
        self.core.set_input_value('시간', minutes)
        self.core.set_input_value('종목조건', jongmok_type)
        self.core.set_input_value('가격구분', price_type)
        return self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)
