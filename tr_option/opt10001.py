#!/usr/bin/env python
# -*- coding: utf-8 -*-

# [ opt10001 : 주식기본정보요청 ]
from copy import deepcopy

from tr_option.base import KWTR


class Opt10001(KWTR):

    def __init__(self, core):
        super().__init__(core)

        self.tr_code = 'opt10001'
        self.rq_name = '주식기본정보요청'

        self.record_name_single = '주식기본정보'
        self.header_single = [
            '종목코드', '종목명', '결산월', '액면가', '자본금', '상장주식', '신용비율',
            '연중최고', '연중최저', '시가총액', '시가총액비중', '외인소진률', '대용가',
            'PER', 'EPS', 'ROE', 'PBR', 'EV', 'BPS', '매출액', '영업이익', '당기순이익',
            '250최고', '250최저', '시가', '고가', '저가', '상한가', '하한가', '기준가',
            '예상체결가', '예상체결수량', '250최고가일', '250최고가대비율', '250최저가일', '250최저가대비율',
            '현재가', '대비기호', '전일대비', '등락율', '거래량', '거래대비', '액면가단위', '유통주식', '유통비율',
        ]

    def tr_opt(self, code, prev_next, screen_no):
        # 종목코드 = 전문 조회할 종목코드

        self.core.set_input_value('종목코드', code)
        return self.core.comm_rq_data(self.rq_name, self.tr_code, prev_next, screen_no)
