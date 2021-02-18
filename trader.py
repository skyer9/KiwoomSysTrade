#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import KWCore
from tr_option.opt10001 import Opt10001


class KWTrader(KWCore):

    def initialize(self):
        self.tr_list['opt10001'] = Opt10001(self)

    def connection(self):
        self.comm_connect()
        return self.response_connect_status

    # [ opt10001 : 주식기본정보요청 ]
    def opt10001(self, code, prev_next, screen_no):
        return self.tr_list['opt10001'].tr_opt(code, prev_next, screen_no)
