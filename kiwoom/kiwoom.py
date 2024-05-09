import os
import sys

from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *
from config.kiwoomType import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print("Kiwoom 클래스 입니다.")

        self.realType = RealType()                  # kiwoomType Realtype, sendtype 정의

        #######event loop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        self.calculator_event_loop = QEventLoop()

        ################ 스크린 번호 모음
        self.screen_my_info= "2000"
        self.screen_calculation_stock = "4000"

        self.screen_real_stock = "5000"
        self.screen_meme_stock = "6000"

        self.screen_start_stop_real = "1000"

        ############ 계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5

        ############ 변수 모음
        self.account_stock_dict = {}
        self.not_account_stock_dict = {}
        self.portfolio_stock_dict = {}
        self.jango_dict = {}                ####'계좌평가잔고내역' jango dict 따로 만든 이유는 hts에서도 따로 되어있기 때문에 맞춰준 겁니다~
        #############################

        ############ 종목 분석 용
        self.calcul_data= []

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()                 #왜 실행을 안하나 했는데 누락되어있었음 59.

        self.signal_login_commConnect()
        self.get_account_info()                 #계좌번호 조회
        self.detail_account_info()              #에수금 가져오는 것
        self.detail_account_mystock()           #계좌평가 잔고 내역 요청
        self.not_concluded_account()            #미체결 요청

        self.read_code()                       #저장된 종목들 불러온다.
        self.screen_number_setting()            #스크린 번호를 할당

        self.dynamicCall("SetRealReg(Qstring, Qstring, Qstring, Qstring)", self.screen_start_stop_real,'', self.realType.REALTYPE['장시작시간']['장운영구분'],"0")

        for code in self.portfolio_stock_dict.keys():                       #지금 포트폴리오 딕트에서 정보들을 다 모아놨으니, 그 값에따른 실시간 정보를 fid 및 스크린번호로 정보를 불러오는것
            screen_num = self.portfolio_stock_dict[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num,code, fids, "1")
            print("실시간 등록 코드: %s, 스크린번호 : %s, 번호: %s" % (code,screen_num,fids))



        #개발가이드 조건검색 KOASTUDIO


#        self.calculator_fnc()               # 종목 분석용, 임시용으로 실행 100까지했을때 과한조회로 막힘

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)      #TR 요청. KOA Studio로 확인. 39강
        self.OnReceiveMsg.connect(self.msg_slot)            #요청하는 모든것이 시그널이 됨, 키움에서 정보를 처리하고있는지 확인하는 메세지용도.

    def real_event_slots(self):                              #실시간 데이터 요청 슬롯 (실시간 데이터들을 다 받아오는듯)
        self.OnReceiveRealData.connect(self.realdata_slot)
        self.OnReceiveChejanData.connect(self.chejan_slot)     #주문을 받는 슬롯

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
        print("미체결 요청")
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
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
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


        if "주식일봉차트조회" == sRQName:

            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
            code = code.strip()
            print(" %s 일봉데이터요청" % code)

            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            print("데이터일수 %s " % cnt)


            # data = self.dynamicCall("GetCommDataEx (Qstring,Qstring)",sTrCode, sRQName)
            # [['', '현재가' , '거래량' , '거래대금' , '날짜' , '시가', '고가', '저가', '']
            #한번 조회하면 600일치까지 일봉데이터를 받을 수 있다.

            for i in range(cnt) :
                data = []

                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")
                value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량")
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가")
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가")
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가")

                data.append("")
                data.append(current_price.strip())
                data.append(value.strip())
                data.append(trading_value.strip())
                data.append(date.strip())
                data.append(start_price.strip())
                data.append(high_price.strip())
                data.append(low_price.strip())
                data.append("")

                self.calcul_data.append(data.copy())

            #print(self.calcul_data)

            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)

            else:

                print("총일수 %s " % len(self.calcul_data))

                pass_success = False

                # 120일 이평선을 그릴만큼의 데이터가 있는지 체크
                if self.calcul_data == None or len(self.calcul_data) < 120:
                    pass_success = False

                else:
                    #120일 이상 되면은

                    total_price = 0
                    for value in self.calcul_data[:120]:
                        total_price += int(value[1])

                    moving_average_price = total_price / 120


                    #오늘자 주가가 120일 이평선에 걸쳐있는지 확인
                    bottom_stock_price = False
                    check_price = None

                    if int(self.calcul_data[0][7]) <= moving_average_price and moving_average_price <= int(self.calcul_data[0][6]):
                        print("오늘 주가 120이평선에 걸쳐있는 것 확인")
                        bottom_stock_price = True
                        check_price = int(self.calcul_data[0][6])

                    #과거 일봉들이 120일 이평선보다 밑에 있는지 확인,
                    # 그렇게 확인을 하다가 일봉이 120일 이평선보다 위에있으면 계산 진행
                    prev_price = None #과거의 일봉 저가
                    if bottom_stock_price == True:

                        moving_average_price_prev = 0
                        price_top_moving = False

                        idx = 1
                        while True:

                            if len(self.calcul_data[idx:]) < 120: #120일치가 있는지 계속 확인
                                print("120일치가 없음!")
                                break

                            total_price = 0
                            for value in self.calcul_data[idx:120+idx]:
                                total_price += int(value[1])
                            moving_average_price_prev = total_price / 120

                            if moving_average_price_prev <= int(self.calcul_data[idx][6]) and idx <= 20:
                                print("20일 동안 주가가 120일 이평선과 같거나 위에 있으면 조건 통과 못함")
                                price_top_moving = False
                                break

                            elif int(self.calcul_data[idx][7]) > moving_average_price_prev and idx > 20 :
                                print("120일 이평선 위에 있는 일봉 확인됨")
                                price_top_moving = True
                                prev_price = int(self.calcul_data[idx][7])
                                break

                            idx += 1

                        #해당 부분 이평선이 가장 최근 일자의 이평선 가격보다 낮은지 확인
                        if price_top_moving == True:
                            if moving_average_price_prev > moving_average_price_prev and check_price > prev_price:
                                print("포착된 이평선의 가격이 오늘자(최근일자 이평선 가격보다 낮은 것 확인됨")
                                print("포착된 부분의 일봉 저가가 오늘자 일봉의 고가보다 낮은지 확인됨")
                                pass_success = True
                if pass_success == True:
                    print("조건부 통과됨")

                    code_nm = self.dynamicCall("GetmasterCodeName(QString)",code)

                    f = open("files/condition_stock.txt", "a", encoding="utf-8")
                    f.write("%s\t%s\t%s\n" % (code, code_nm, str(self.calcul_data[0][1])))
                    f.close()

                elif pass_success == False:
                    print("조건부 통과 못함")

                self.calcul_data.clear()
                self.calculator_event_loop.exit()


    def get_code_list_by_market(self,market_code):
        '''
        종목 코드들 반환
        :param market_code:
        :return:
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)",market_code)
        code_list = code_list.split(";")[:-1]

        return code_list

    def calculator_fnc(self):
        '''
        종목 분석 실행용 함수
        :return:
        '''
        code_list = self.get_code_list_by_market("10")
        print("코스닥 갯수 %s" % len(code_list))



        for idx, code in enumerate(code_list):

            self.dynamicCall("DisconnectRealData(Qstring)",self.screen_calculation_stock)

            print("%s / %s : KOSDAQ Stock Code : %s is updating... " % (idx+1, len(code_list), code))

            self.day_kiwoom_db(code=code)


    def day_kiwoom_db(self, code=None, date=None, sPrevNext="0"):

        QTest.qWait(3600)

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)

        self.calculator_event_loop.exec_()



    def read_code(self):

        if os.path.exists("files/condition_stock.txt"): # == true
            f = open("files/condition_stock.txt", "r", encoding="utf-8")

            lines = f.readlines()  # 파일안에 종목 여러개일 경우에 모든걸 가져옴
            for line in lines:       #for 문을 통해 하나하나 읽음
                if line != "":        #line 이 비어있지 않을경우
                    ls = line.split("\t")  #tab 을 기준으로 분리하여 리스트에 저장 ["203947", "종목명", "현재가]

                    stock_code = ls[0]
                    stock_name = ls[1]
                    stock_price = ls[2].split("\n")[0]  # \n 을 제거k
                    stock_price = abs(int(stock_price))      #|-1| = 1 절대값

                    self.portfolio_stock_dict.update({stock_code:{"종목명": stock_name, "현재가" : stock_price}})
                    #portfolio_stock_dict 에 종목들 업데이트 예정.
            f.close()           #파일이 열려있는 상태로 닫아줘야함
            print(self.portfolio_stock_dict)


    def screen_number_setting(self):

        screen_overwrite = []

        #계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #미체결에 있는 종목들
        for order_number in self.not_account_stock_dict.keys():
            code = self.not_account_stock_dict[order_number]['종목코드']

            if code not in screen_overwrite:
                screen_overwrite.append(code)

        #포트폴리오에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)


        #스크린번호 할당
        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0 :
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0 :
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].update({"주문용스크린번호": str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict.update({code: {"스크린번호":str(self.screen_real_stock) ,"주문용스크린번호":str(self.screen_meme_stock)}})
                # 포트폴리오에 없는 주식인 경우, 스크린 번호와 주문용 스크린 번호를 함께 할당


                cnt += 1

        print(self.portfolio_stock_dict)


    def realdata_slot(self, sCode, sRealType, sRealData):           # 실시간 데이터 수집

        if sRealType == "장시작시간" :
            fid = self.realType.REALTYPE[sRealType]['장운영구분']
            value = self.dynamicCall("GetCommRealData(Qstring, int)", sCode, fid)

            if value == '0':
                print("장 시작 전")

            elif value == '3':
                print("장 시작")

            elif value == '2':
                print("장 종료, 동시호가로 넘어감")

            elif value == '4':
                print("3시30분 장 종료")

                for code in self.portfolio_stock_dict.keys():
                    self.dynamicCall("SetRealRemove(String, String)", self.portfolio_stock_dict[code]['스크린번호'],code)

                    QTest.qWait(5000)

                self.file_delete()              ##분석파일삭제
                self.calculator_fnc()           ##분석시작

                sys.exit()

            ## GetCommRealData 로 fid 215 불러오고 , 그 값이 0인지 3인지 2인지 4인지 정보를 어디서봐야하나
            elif value == '8':
                print("장장 마감")

            elif value == '9':
                print("장 마감")


        elif sRealType == "주식체결":       #틱이 생길때마다 Code 를 프린트하는거같음.
            print(sCode)

            a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간']) #HMMSSS

            b = self.dynamicCall("GetCommRealData(QString, int)", sCode,self.realType.REALTYPE[sRealType]['현재가'])  # +(-) 2500
            b = abs(int(b))

            c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['전일대비'])
            c = abs(int(c))

            d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['등락율'])
            d = float(d)

            e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가']) #출력: +(-)2520
            e = abs(int(e))

            f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가']) #출력 : +(-)2515
            f = abs(int(f))

            g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['거래량'])  #출력 : +240124 매수일때, -203403 매도일때
            g = abs(int(g))

            h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['누적거래량'])  #출력 : 240124
            h = abs(int(h))

            i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['고가'])  #출력 : 240124
            i = abs(int(i))

            j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['시가'])  #출력 : 240124
            j = abs(int(j))

            k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])  #출력 : 240124
            k = abs(int(k))

            if sCode not in self.portfolio_stock_dict:            #실시간으로 sCode 를받아오는거같은데.
                self.portfolio_stock_dict.update({sCode:{}})

            self.portfolio_stock_dict[sCode].update({"체결시간" : a})
            self.portfolio_stock_dict[sCode].update({"현재가": b})
            self.portfolio_stock_dict[sCode].update({"전일대비" : c})
            self.portfolio_stock_dict[sCode].update({"등락율" : d})
            self.portfolio_stock_dict[sCode].update({"(최우선)매도호가" : e})
            self.portfolio_stock_dict[sCode].update({"(최우선)매수호가" : f})
            self.portfolio_stock_dict[sCode].update({"거래량": g})
            self.portfolio_stock_dict[sCode].update({"누적거래량" : h})
            self.portfolio_stock_dict[sCode].update({"고가" : i})
            self.portfolio_stock_dict[sCode].update({"시가" : j})
            self.portfolio_stock_dict[sCode].update({"저가" : k})

            print(self.portfolio_stock_dict[sCode])

            # 계좌잔고평가내역에 있고 오늘 산 잔고에는 없을 경우 (계좌평가잔고내역 안)
            if sCode in self.account_stock_dict.keys() and sCode not in self.jango_dict.keys():
                asd = self.account_stock_dict[sCode]

                meme_rate = (b - asd['매입가']) / asd['매입가'] * 100     # 구매한 종목의 현재 수익률

                if asd['매매가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5):
                    order_success = self.dynamicCall("SendOrder(QString, QString, Qstring, int, QString, int, int, QString, QString)",
                                                     ["신규매도", self.portfolio_stock_dict[sCode]['주문용스크린번호'], self.account_num, 2,
                                                     sCode, asd['매매가능수량'], 0, self.realType.SENDTYPE['거래구분']['시장가'], ""])   ###주문을하는것

                    if order_success ==0:
                        print("매도주문 전달 성공")
                        del self.account_stock_dict[sCode]

                    else :                             ### 에러코드들이 나올것임  여기서 else 는 조건이필요없었고, elif 는 조건이있어야함
                        print("매도주문 전달 실패")

            # 오늘 산 잔고에 있을 경우
            elif sCode in self.jango_dict.keys():
                #print("%s %s" % ("신규매도를한다2", sCode))
                jd = self.jango_dict[sCode]         # 잔고 딕셔너리를 게속 찾아오려면 일이기때문에 정의시킴
                meme_rate = (b - jd['매입단가']) / jd['매입단가'] * 100     #매입단가를 가지고 얼만큼 올랐는지

                if jd['주문가능수량'] > 0 and (meme_rate > 5 or meme_rate < -5): #주문가능수량이 0보다크고 오른수치가 5프로 ~ -5프로 사이 인지

                    order_success = self.dynamicCall("SendOrder(QString, QString, Qstring, int, int, int, QString, QString)",
                                                     ["신규매도",self.portfolio_stock_dict[sCode]["주문용스크린번호"],self.account_num,2, sCode, jd['주문가능수량'],
                                                      0, self.realType.SENDTYPE['거래구분']['시장가'],""]
                                                     )   #2: 신규매도 ,시장가로 매도
                    if order_success == 0:
                        self.logging.logger.debug("매도주문 전달 성공")
                    else:
                        self.logging.logger.debug("매도주문 전달 실패")

            # 등락율이 2.0% 이상이고 오늘 산 잔고에 없을 경우
            elif d > 2.0 and sCode not in self.jango_dict:
                print("%s %s" % ("신규매수를한다", sCode))

                result = (self.use_money * 0.1) / e         ## 예수금의 * 0.1  나누기 e(현재가)
                quantity = int(result)                      ## 몫이나오면 그만큼 사겠다 소수점은 int 로바꿈

                order_success = self.dynamicCall(
                    "SendOrder(QString, QString, Qstring, int, int, int, QString, QString)",
                                                     ["신규매수",self.portfolio_stock_dict[sCode]["주문용스크린번호"],self.account_num,1, sCode, quantity,
                                                      self.realType.SENDTYPE['거래구분']['지정가'],""]
                                                     )   #1:신규매수, 2:신규매도 ,지정가로 매수

                if order_success == 0:
                    self.logging.logger.debug("매수주문 전달 성공")
                else:
                    self.logging.logger.debug("매수주문 전달 실패")



            not_meme_list = list(self.not_account_stock_dict)    #dict 에  list 를 씌운것으로 , dict 의 주솟값을 따로 가져감. 같이변동되지않음 copy 를 사용해도 동일

            for order_num in not_meme_list:     #실시간이므로 5개종목에서 6개로 바뀌었을때 에러가남 , 그래서 카피 또는 list 로 주솟값을 변경해서 사용
                code = self.not_account_stock_dict[order_num]["종목코드"]
                meme_price = self.not_account_stock_dict[order_num]['주문가격']
                not_quantity = self.not_account_stock_dict[order_num]['미체결수량']
                order_gubun = self.not_account_stock_dict[order_num]['주문구분']

                if order_gubun == "매수" and not_quantity > 0 and e > meme_price:
                   # print("%s %s" % ("매수취소 한다", sCode))
                    order_success = self.dynamicCall(
                    "SendOrder(QString, QString, Qstring, int, int, int, QString, QString)",
                                                     ["매수취소",self.portfolio_stock_dict[sCode]["주문용스크린번호"],self.account_num, 3, code, 0, 0,
                                                      self.realType.SENDTYPE['거래구분']['지정가'], order_num]
                                                     )   #1:신규매수, 2:신규매도 ,전량 매수취소
                    if order_success == 0:
                        self.logging.logger.debug("매수취소 전달 성공")
                    else:
                        self.logging.logger.debug("매수취소 전달 실패")


                elif not_quantity == 0:                         #미체결 수량이 0 일경우 주문번호 삭제
                    del self.not_account_stock_dict[order_num]


    def chejan_slot(self, sGubun, nItemCnt, sFIdList):          #sendOrder 가 들어갈경우 chejan slot으로 데이터가 들어오는상태

        if int(sGubun) == 0 :                                   ## 종목이 매수될때 정보를받아오는부분
            #print("주문체결")
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()

            origin_order_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호']) # 출력 :defaluse : "00023"

            order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호']) # 출력 : 0115061 마지막 주문번호

            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태']) # 출력 : 접수 확인 체결

            order_quan =  self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량']) # 출력 :3
            order_quan = int(order_quan)

            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격']) # 출력 :20000
            order_price = int(order_price)

            not_chegual_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량']) # 출력 : 15 default : 0
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])  # 출력 : -매도,+매수
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            chagual_time_str = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문/체결시간']) #출력 : '151028'

            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가']) # 출력 2110 default

            if chegual_price == '':                 ##처음에 주문넣으면 접수이므로 체결가가 없을거야, 그래서 공백
                chegual_price = 0                    #숫자로 할당
            else :
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량']) # 출력 : 5 default ''

            if chegual_quantity == '':

                chegual_quantity = 0

            else:
                chegual_quantity = int(chegual_quantity)


            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가']) # 출력 : -6000
            current_price = abs(int(current_price))

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매도호가']) # 출력 :-6010

            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매수호가']) # 출력 : -6010

            first_buy_price = abs(int(first_buy_price))

        ###### 새로 들어온 주문이면 주문번호 할당
            if order_number not in self.not_account_stock_dict.keys():
                self.not_account_stock_dict.update({order_number :{}})

            self.not_account_stock_dict[order_number].update({"종목코드" :sCode})
            self.not_account_stock_dict[order_number].update({"주문번호" :order_number})
            self.not_account_stock_dict[order_number].update({"종목명" : stock_name})
            self.not_account_stock_dict[order_number].update({"주문상태": order_status})
            self.not_account_stock_dict[order_number].update({"주문수량" : order_quan})
            self.not_account_stock_dict[order_number].update({"주문가격" : order_price})
            self.not_account_stock_dict[order_number].update({"미체결수량" : not_chegual_quan})
            self.not_account_stock_dict[order_number].update({"원주문번호" : origin_order_name})
            self.not_account_stock_dict[order_number].update({"주문구분" : order_gubun})
            self.not_account_stock_dict[order_number].update({"주문/체결시간" : chagual_time_str})
            self.not_account_stock_dict[order_number].update({"체결가": chegual_price})
            self.not_account_stock_dict[order_number].update({"체결량": chegual_quantity})
            self.not_account_stock_dict[order_number].update({"현재가": current_price})
            self.not_account_stock_dict[order_number].update({"(최우선)매도호가": first_sell_price})
            self.not_account_stock_dict[order_number].update({"(최우선매수호가": first_buy_price})


        elif int(sGubun) == 1 :             ###종목이 매도될때 정보를 받아오는 부분
            #print("잔고")
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'][1:])

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가'])
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode :{}})

            self.jango_dict[sCode].update({"현재가" : current_price})
            self.jango_dict[sCode].update({"종목코드" : sCode})
            self.jango_dict[sCode].update({"종목명" : stock_name})
            self.jango_dict[sCode].update({"보유수량" : stock_quan})
            self.jango_dict[sCode].update({"주문가능수량" : like_quan})
            self.jango_dict[sCode].update({"매입단가" : buy_price})
            self.jango_dict[sCode].update({"총매입가" : total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분" : meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가" : first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가 : first_buy_price"})

            if stock_quan == 0:
                del self.jango_dict[sCode]
                self.dynamicCall("SetRealRemove(QString, QString)", self.portfolio_stock_dict[sCode]['스크린번호'], sCode) #해당종목에 대해서 실시간으로 연결을 끊는다


    #송수신 메세지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        print("스크린: %s, 요청이름: %s, tr코드: %s --- %s" %(sScrNo, sRQName, sTrCode, msg))

    #파일 삭제
    def file_delete(self):                              ##파일삭제
        if os.path.isfile("files/condition_stock.txt"):
            os.remove("files/condition_stock.txt")






