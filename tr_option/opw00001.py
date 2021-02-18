from tr_option.base import KWTR
from copy import deepcopy


# [ opw00001 : 계좌수익률요청 ]
class Opw00001(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opw00001'
        self.rq_name = '계좌수익률요청'

        self.record_name_multiple = '계좌수익률'
        self.header_multiple = [
            '일자', '종목코드', '종목명', '현재가', '매입가', '매입금액', '보유수량', '당일매도손익', '당일매매수수료', '당일매매세금',
            '신용구분', '대출일', '결제잔고', '청산가능수량', '신용금액', '신용이자', '만기일',
        ]

    def tr_opt(self, input0, prev_next, screen_no):
        # 계좌번호 = 전문 조회할 보유계좌번호

        self.core.set_input_value('계좌번호', input0)
        self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)

        self.tr_data = deepcopy(self.core.receive_tr_data_handler[self.tr_code][screen_no])

        return self.tr_data
