#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from sqlalchemy import create_engine, Column, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

DATABASE = create_engine('mysql+mysqldb://root:abcd1234@localhost:3306/db_stock?charset=utf8',
                         echo=False, pool_size=20, pool_recycle=500)

session_factory = sessionmaker(bind=DATABASE)
Session = scoped_session(session_factory)

Base = declarative_base()


class StockBasicInfo(Base):
    __tablename__ = 'tbl_stock_basic_info'

    종목코드 = Column(String(6), primary_key=True)
    종목명 = Column(String(128), nullable=False)
    regdate = Column(DateTime)
    lastupdate = Column(DateTime)

    def __init__(self, stock_code, stock_name):
        self.종목코드 = stock_code
        self.종목명 = stock_name
        self.regdate = datetime.now()
        self.lastupdate = datetime.now()

    def __repr__(self):
        return "<StockBasicInfo('%s', '%s')>" % (self.종목코드, self.종목명)


class StockDayCandleChart(Base):
    __tablename__ = 'tbl_stock_day_candle_chart'

    종목코드 = Column(String(6), primary_key=True)
    일자 = Column(String(8), primary_key=True)
    현재가 = Column(Numeric(10, 2), nullable=False)
    거래량 = Column(Numeric(15, 2), nullable=False)
    거래대금 = Column(Numeric(15, 2), nullable=False)
    시가 = Column(Numeric(10, 2), nullable=False)
    고가 = Column(Numeric(10, 2), nullable=False)
    저가 = Column(Numeric(10, 2), nullable=False)
    regdate = Column(DateTime)
    lastupdate = Column(DateTime)

    def __init__(self, 종목코드, 현재가, 거래량, 거래대금, 일자, 시가, 고가, 저가):
        self.종목코드 = 종목코드
        self.현재가 = 현재가
        self.거래량 = 거래량
        self.거래대금 = 거래대금
        self.일자 = 일자
        self.시가 = 시가
        self.고가 = 고가
        self.저가 = 저가
        self.regdate = datetime.now()
        self.lastupdate = datetime.now()

    def __repr__(self):
        return "<StockDayCandleChart('%s', '%s')>" % (self.종목코드, self.일자)
