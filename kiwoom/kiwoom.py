from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print("Kiwoom 클래스 입니다.")
        #######event loop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()

        ################ 스크린 번호 모음
        self.screen_my_info= "2000"


        ############ 계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5

        ############ 변수 모음
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        #############################


        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()              #에수금 가져오는 것
        self.detail_account_mystock()           #계좌평가 잔고 내역 요청
        self.not_concluded_account()


    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)      #TR 요청. KOA Studio로 확인. 39강

    def login_slot(self,errCode):                   #슬롯
        print(errors(errCode))

        self.login_event_loop.exit()                #로그인 완료시 exit


    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()        #이벤트루프
        self.login_event_loop.exec_()               #로그인이 완료 될때까지 다음게 실행안되게 막음 b

    def get_account_info(self):
        account_list = self.dynamicCall(("GetLoginInfo(String)"),"ACCNO")

        self.account_num = account_list.split(';')[0]                  #계좌 리스트 중 ; 로나눠서 리스트로 만듬,

        print("나의 보유 계좌번호 %s " % self.account_num)                 #8074761211


    def detail_account_info(self):                             ##예수금상세 TR 목록  (KOA 의 opw00001 에 정보 입력하여 TR요청을하고)
        print("예수금 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00") # 함수 호출이므로 리스트 딕셔너리 구분이 무의미함
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청","OPW00001","0", self.screen_my_info )     # 0 = preNext, ScreenNumber

        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        print("계좌평가 잔고내역 요청하기 연속조회 %s " % sPrevNext)

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")  # 함수 호출이므로 리스트 딕셔너리 구분이 무의미함
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청","OPW00018",sPrevNext, self.screen_my_info)     # 0 = preNext, ScreenNumber


        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0" ):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        ## 보류  self.dynamicCall("SetInputValue(QString, QString)", "종목코드", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):    #(detail_account_info 에서 요청한 값을 받아서 PreNext 는 0또는2
        '''
        tr요청을 받는 구역이다! 슬롯이다!
        :param self:
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을 때 지은 이름
        :param sTrCode: 요청 id,tr 코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청" :
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금") #이벤트루프에서 데이터를 빼옴
            print("예수금 %s " % deposit)
            print("예수금 형변환%s" % int(deposit))  #000000을삭제하기위해 int 로 변환

            self.use_money = int(deposit) * self.use_money_percent
            self.use_money = self.use_money / 4

            ok_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(ok_deposit))


            self.detail_account_info_event_loop.exit()


        if sRQName == "계좌평가잔고내역요청" :

            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)

            print("총 매입 금액 %s" % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)

            print("총수익률(%s) : %s" %("%", total_profit_loss_rate_result))

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)  ##보유종목 갯수 측정
            cnt = 0

            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code = code.strip()[1:] ## strip   "   양쪽공백 제거    " 1은 0번다음 1부터 끝까지

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")

                if code in self.account_stock_dict:           ##종목명이 있을경우 패스
                    pass
                else:                                   ##종목명이 없을경우 dictionaly 에 넣어줌
                    self.account_stock_dict.update({code:{}})


                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())                  ###수익률은 소수점까지
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())


                self.account_stock_dict[code].update({"종목명": code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({'매매가능수량': possible_quantity})


                cnt += 1

                #####print dictionary 할경우 종목명등등 다 나옴
            print("계좌에 가지고 있는 종목 %s" % self.account_stock_dict)
            print("계좌에 보유종목 카운트%s" % cnt)


            

            if sPrevNext == "2":                    ###sPrevNext 가 없어진거같음
                self.detail_account_mystock(sPrevNext="2")
                print("yes")
            else :
                self.detail_account_info_event_loop.exit()
                print("no")


        if sRQName == "실시간미체결요청" :

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)

            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태")  # 접수 -> 확인 -> 체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량")  # 수정
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분")
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')       ## "+"나 "-" 기호를 제거합니다.
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}                   ## 주문번호가 없으면 orde_no 딕셔너리를 생성

                self.not_account_stock_dict[order_no].update({"종목코드": code})
                self.not_account_stock_dict[order_no].update({'종목명' : code_nm})
                self.not_account_stock_dict[order_no].update({'주문번호' : order_no})
                self.not_account_stock_dict[order_no].update({'주문상태' : order_status})
                self.not_account_stock_dict[order_no].update({'주문수량':order_quantity})
                self.not_account_stock_dict[order_no].update({'주문가격' : order_price})
                self.not_account_stock_dict[order_no].update({'주문구분' : order_gubun})
                self.not_account_stock_dict[order_no].update({'미체결수량' : not_quantity})
                self.not_account_stock_dict[order_no].update({'체결량' : ok_quantity})

                print("미체결 종목: %s " % self.not_account_stock_dict[order_no])

            self.detail_account_info_event_loop.exit()
            print("2024-04-25 미체결출력")






