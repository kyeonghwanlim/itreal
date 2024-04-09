from kiwoom.kiwoom import *

import sys                                  ##파이썬 시스템 라이브러리


from PyQt5.QtWidgets import *               ##PyQt ui적인거 꾸밀때 사용


class Ui_calss():                           ## 클래스의 앞글자는 대문자로
    def __init__(self):
        print("UI_class 입니다")

        self.app = QApplication(sys.argv)   ##sys.argv 리스트형태로 인자들이 들어있음['파이썬파일경로',추가할옵션','---]

        Kiwoom()

        self.app.exec_()                    ##증권프로그램 안꺼지게 이벤트루프