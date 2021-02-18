from abc import abstractmethod

from core import KWCore


class KWTR(object):
    tr_data = ''
    rq_name = tr_code = ''

    record_name_single = ''
    record_name_multiple = ''

    header_single = []
    header_multiple = []

    def __init__(self, core):
        assert (isinstance(core, KWCore))
        self.core = core

    @abstractmethod
    def tr_opt(self, code, prev_next, screen_no):
        pass

    # 싱글데이터 전용
    def tr_opt_data(self, tr_code, rq_name, index):
        if self.header_single:
            ret = {
                'header': self.header_single,
                'rows': [self.core.get_comm_data(tr_code, rq_name, index, column) for column in self.header_single],
            }

        return ret

    def tr_opt_data_ex(self, tr_code, rq_name):
        ret = {
            'header': self.header_multiple,
            'rows': self.core.get_comm_data_ex(tr_code, rq_name),
        }

        return ret
