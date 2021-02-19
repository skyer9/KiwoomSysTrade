#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import KWCore
from tr_option.opt10001 import Opt10001
from tr_option.opt10004 import Opt10004
from tr_option.opt10059 import Opt10059
from tr_option.opt10080 import Opt10080
from tr_option.opt10081 import Opt10081
from tr_option.opt10082 import Opt10082
from tr_option.opt10085 import Opt10085
from tr_option.opt20006 import Opt20006


class KWTrader(KWCore):

    def initialize(self):
        self.tr_list['opt10001'] = Opt10001(self)
        self.tr_list['opt10004'] = Opt10004(self)
        self.tr_list['opt10059'] = Opt10059(self)
        self.tr_list['opt10080'] = Opt10080(self)
        self.tr_list['opt10081'] = Opt10081(self)
        self.tr_list['opt10082'] = Opt10082(self)
        self.tr_list['opt10085'] = Opt10085(self)

        self.tr_list['opt20006'] = Opt20006(self)

    def connection(self):
        return self.comm_connect()
        # return self.response_connect_status

    # [ opt10001 : 주식기본정보요청 ]
    def opt10001(self, code, prev_next, screen_no):
        return self.tr_list['opt10001'].tr_opt(code, prev_next, screen_no)

    # [ opt10004 : 주식호가요청 ]
    def opt10004(self, code, prev_next, screen_no):
        return self.tr_list['opt10004'].tr_opt(code, prev_next, screen_no)

    # [ opt10059 : 종목별투자자기관별요청 ]
    def opt10059(self, date, code, input2, input3, input4, prev_next, screen_no):
        return self.tr_list['opt10059'].tr_opt(date, code, input2, input3, input4, prev_next, screen_no)

    # [ opt10080 : 주식분봉차트조회요청 ]
    def opt10080(self, code, tick_range, fix, prev_next, screen_no):
        return self.tr_list['opt10080'].tr_opt(code, tick_range, fix, prev_next, screen_no)

    # [ opt10081 : 주식일봉차트조회요청 ]
    def opt10081(self, code, date_from, input2, prev_next, screen_no):
        return self.tr_list['opt10081'].tr_opt(code, date_from, input2, prev_next, screen_no)

    # [ opt10082 : 주식주봉차트조회요청 ]
    def opt10082(self, code, date_from, date_to, input3, prev_next, screen_no):
        return self.tr_list['opt10082'].tr_opt(code, date_from, date_to, input3, prev_next, screen_no)

    # [ opt10085 : 계좌수익률요청 ]
    def opt10085(self, account_no, prev_next, screen_no):
        return self.tr_list['opt10085'].tr_opt(account_no, prev_next, screen_no)

    # [ opt20006 : 업종일봉조회요청 ]
    def opt20006(self, input0, input1, prev_next, screen_no):
        return self.tr_list['opt20006'].tr_opt(input0, input1, prev_next, screen_no)
