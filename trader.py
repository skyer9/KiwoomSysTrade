#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import KWCore
from tr_option.opt10001 import Opt10001
from tr_option.opt10080 import Opt10080
from tr_option.opt10085 import Opt10085


class KWTrader(KWCore):

    def initialize(self):
        self.tr_list['opt10001'] = Opt10001(self)
        self.tr_list['opt10080'] = Opt10080(self)
        self.tr_list['opt10085'] = Opt10085(self)

    def connection(self):
        self.comm_connect()
        return self.response_connect_status

    # [ opt10001 : 주식기본정보요청 ]
    def opt10001(self, code, prev_next, screen_no):
        return self.tr_list['opt10001'].tr_opt(code, prev_next, screen_no)

    # [ opt10080 : 주식분봉차트조회요청 ]
    def opt10080(self, code, tick_range, fix, prev_next, screen_no):
        return self.tr_list['opt10080'].tr_opt(code, tick_range, fix, prev_next, screen_no)

    # [ opt10085 : 계좌수익률요청 ]
    def opt10085(self, account_no, prev_next, screen_no):
        return self.tr_list['opt10085'].tr_opt(account_no, prev_next, screen_no)