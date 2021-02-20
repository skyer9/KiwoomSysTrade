#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core import KWCore
from tr_option.opt10001 import Opt10001
from tr_option.opt10004 import Opt10004
from tr_option.opt10023 import Opt10023
from tr_option.opt10059 import Opt10059
from tr_option.opt10080 import Opt10080
from tr_option.opt10081 import Opt10081
from tr_option.opt10082 import Opt10082
from tr_option.opt10085 import Opt10085
from tr_option.opt20006 import Opt20006
from tr_option.opw00001 import Opw00001


class KWTrader(KWCore):

    def initialize(self, logger):
        self.tr_list['opt10001'] = Opt10001(self)
        self.tr_list['opt10004'] = Opt10004(self)
        self.tr_list['opt10023'] = Opt10023(self)
        self.tr_list['opt10059'] = Opt10059(self)
        self.tr_list['opt10080'] = Opt10080(self)
        self.tr_list['opt10081'] = Opt10081(self)
        self.tr_list['opt10082'] = Opt10082(self)
        self.tr_list['opt10085'] = Opt10085(self)

        self.tr_list['opt20006'] = Opt20006(self)

        self.tr_list['opw00001'] = Opw00001(self)

        self.logger = logger

    def login(self):
        return self.comm_connect()
