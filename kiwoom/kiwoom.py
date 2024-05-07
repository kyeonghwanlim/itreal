import os

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

    def real_event_slots(self):                              #실시간 데이터 요청 슬롯 (실시간 데이터들을 다 받아오는듯)
        self.OnReceiveRealData.connect(self.realdata_slot)


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

        QTest.qWait(1800)

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
            ## GetCommRealData 로 fid 215 불러오고 , 그 값이 0인지 3인지 2인지 4인지 정보를 어디서봐야하나


        elif sRealType == "주식체결":       #틱이 생길때마다 Code 를 프린트하는거같음.
            print(sCode)
