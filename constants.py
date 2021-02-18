from enum import Enum


class KWCode(object):
    def __init__(self, code_id, code_name, description):
        """
        Args:
            code_id     (int) : 리턴 코드
            code_name   (str) : 리턴 코드명
            description (str) : 설명
        """
        self.code_id = code_id
        self.code_name = code_name
        self.description = description

    def __str__(self):
        if self.description:
            return "%s, %s : %s" % (self.code_id, self.code_name, self.description)
        else:
            return "%s, %s" % (self.code_id, self.code_name)

    def __eq__(self, other):
        if type(other) is KWCode:
            if self.code_id == other.code_id \
                    or self.code_name == other.code_name:
                return True
        elif type(other) is int:
            if self.code_id == other:
                return True

        return False


class KWErrorCode(Enum):
    OP_ERR_NONE = KWCode(0, 'OP_ERR_NONE', '정상처리')
    OP_ERR_FAIL = KWCode(-10, 'OP_ERR_FAIL', '실패')
    OP_ERR_COND_NOT_FOUND = KWCode(-11, 'OP_ERR_COND_NOT_FOUND', '조건번호없음')
    OP_ERR_COND_MISMATCH = KWCode(-12, 'OP_ERR_COND_MISMATCH', '조건번호와조건식 틀림')
    OP_ERR_COND_OVERFLOW = KWCode(-13, 'OP_ERR_COND_OVERFLOW', '조건검색조회요청 초과')
    OP_ERR_LOGIN = KWCode(-100, 'OP_ERR_LOGIN', '사용자정보교환실패')
    OP_ERR_CONNECT = KWCode(-101, 'OP_ERR_CONNECT', '서버접속 실패')
    OP_ERR_VERSION = KWCode(-102, 'OP_ERR_VERSION', '버전처리실패')
    OP_ERR_FIREWALL = KWCode(-103, 'OP_ERR_FIREWALL', '개인방화벽실패')
    OP_ERR_MEMORY = KWCode(-104, 'OP_ERR_MEMORY', '메모리보호 실패')
    OP_ERR_INPUT = KWCode(-105, 'OP_ERR_INPUT', '함수입력값오류')
    OP_ERR_SOCKET_CLOSED = KWCode(-106, 'OP_ERR_SOCKET_CLOSED', '통신연결종료')
    OP_ERR_SISE_OVERFLOW = KWCode(-200, 'OP_ERR_SISE_OVERFLOW', '시세조회과부하')
    OP_ERR_RQ_STRUCT_FAIL = KWCode(-201, 'OP_ERR_RQ_STRUCT_FAIL', '전문작성초기화 실패')
    OP_ERR_RQ_STRING_FAIL = KWCode(-202, 'OP_ERR_RQ_STRING_FAIL', '전문작성입력값 오류')
    OP_ERR_NO_DATA = KWCode(-203, 'OP_ERR_NO_DATA', '데이터없음')
    OP_ERR_OVER_MAX_DATA = KWCode(-204, 'OP_ERR_OVER_MAX_DATA', '조회가능한 종목수 초과')
    OP_ERR_DATA_RCV_FAIL = KWCode(-205, 'OP_ERR_DATA_RCV_FAIL', '데이터수신실패')
    OP_ERR_OVER_MAX_FID = KWCode(-206, 'OP_ERR_OVER_MAX_FID', '조회가능한 FID 수초과')
    OP_ERR_REAL_CANCEL = KWCode(-207, 'OP_ERR_REAL_CANCEL', '실시간해제 오류')
    OP_ERR_ORD_WRONG_INPUT = KWCode(-300, 'OP_ERR_ORD_WRONG_INPUT', '입력값오류')
    OP_ERR_ORD_WRONG_ACCTNO = KWCode(-301, 'OP_ERR_ORD_WRONG_ACCTNO', '계좌비밀번호 없음')
    OP_ERR_OTHER_ACC_USE = KWCode(-302, 'OP_ERR_OTHER_ACC_USE', '타인계좌사용 오류')
    OP_ERR_MIS_2BILL_EXC = KWCode(-303, 'OP_ERR_MIS_2BILL_EXC', '주문가격이 20 억원을 초과')
    OP_ERR_MIS_5BILL_EXC = KWCode(-304, 'OP_ERR_MIS_5BILL_EXC', '주문가격이 50 억원을 초과')
    OP_ERR_MIS_1PER_EXC = KWCode(-305, 'OP_ERR_MIS_1PER_EXC', '주문수량이 총발행주수의 1% 초과오류')
    OP_ERR_MIS_3PER_EXC = KWCode(-306, 'OP_ERR_MIS_3PER_EXC', '주문수량이 총발행주수의 3% 초과오류')
    OP_ERR_SEND_FAIL = KWCode(-307, 'OP_ERR_SEND_FAIL', '주문전송실패')
    OP_ERR_ORD_OVERFLOW0 = KWCode(-308, 'OP_ERR_ORD_OVERFLOW', '주문전송과부하')
    OP_ERR_MIS_300CNT_EXC = KWCode(-309, 'OP_ERR_MIS_300CNT_EXC', '주문수량 300 계약 초과')
    OP_ERR_MIS_500CNT_EXC = KWCode(-310, 'OP_ERR_MIS_500CNT_EXC', '주문수량 500 계약 초과')
    OP_ERR_ORD_OVERFLOW1 = KWCode(-311, 'OP_ERR_ORD_OVERFLOW', '주문전송과부하')
    OP_ERR_ORD_WRONG_ACCTINFO = KWCode(-340, 'OP_ERR_ORD_WRONG_ACCTINFO', '계좌정보없음')
    OP_ERR_ORD_SYMCODE_EMPTY = KWCode(-500, 'OP_ERR_ORD_SYMCODE_EMPTY', '종목코드없음')

    def __str__(self):
        return "%s, %s" % (self.name, self.value)

    def __eq__(self, other):
        if type(other) == KWErrorCode and type(other.value) == KWCode:
            return self.value == other.value
        elif type(other) is int:
            return self.value == other

        return False
