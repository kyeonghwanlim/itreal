from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        print("Kiwoom 클래스 입니다.")
        #######event loop 모음
        self.login_event_loop = None
        #####################

        self.get_ocx_instance()
        self.event_slots()

        self.signal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()              #에수금 가져오는 것

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
        self.login_event_loop.exec_()               #로그인이 완료 될때까지 다음게 실행안되게 막음

    def get_account_info(self):
        account_list = self.dynamicCall(("GetLoginInfo(String)"),"ACCNO")

        self.accoount_num = account_list.split(';')[0]                  #계좌 리스트 중 ; 로나눠서 리스트로 만듬,

        print("나의 보유 계좌번호 %s " % self.accoount_num)                 #8074761211


    def detail_account_info(self):                             ##예수금상세 TR 목록  (KOA 의 opw00001 에 정보 입력하여 TR요청을하고)
        print("예수금 요청하는 부분")
        self.dynamicCall("SetInputValue(String, String)", "계좌번호", self.accoount_num)
        self.dynamicCall("SetInputValue(String, String)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(String, String)", "비밀번호입력매체구분", "00") # 함수 호출이므로 리스트 딕셔너리 구분이 무의미함
        self.dynamicCall("SetInputValue(String, String)", "조회구분", "2")
        self.dynamicCall("CommRqData(String, String, int, String)", "예수금상세현황요청","OPW00001","0", "2000")     # 0 = preNext, ScreenNumber

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):    #(detail_account_info 에서 요청한 값을 받아서
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
            deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "예수금") #이벤트루프에서 데이터를 빼옴
            print("예수금 %s " % deposit)
            int(deposit)                        #000000을삭제하기위해 int 로 변환

            ok_deposit = self.dynamicCall("GetCommData(String, String, int, String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % ok_deposit)
            int(ok_deposit)










