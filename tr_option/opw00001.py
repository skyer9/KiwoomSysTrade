from tr_option.base import KWTR
from copy import deepcopy


# [ opw00001 : 예수금상세현황요청 ]
class Opw00001(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opw00001'
        self.rq_name = '예수금상세현황요청'

        self.record_name_single = '예수금상세현황'
        self.header_single = [
            '예수금', '주문가능금액', '출금가능금액',
        ]

    def tr_opt(self, account_no, prev_next, screen_no):
        # 계좌번호 = 전문 조회할 보유계좌번호

        self.core.set_input_value('계좌번호', account_no)
        self.core.set_input_value('비밀번호', '')
        self.core.set_input_value('비밀번호입력매체구분', '00')
        self.core.set_input_value('조회구분', '2')
        return self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)
