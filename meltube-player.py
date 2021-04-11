from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import time
import sys, os
import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

title_list = []
singer_list = []
play_list = []
dictionary = dict()
called = False

# 쓰레드 선언


class Thread1(QThread):
    # parent = MainWidget을 상속 받음.

    def __init__(self, parent):
        super().__init__(parent)
        self.btn_refresh = parent.btn_refresh
        self.boxlayout = parent.boxlayout

    def run(self):
        global called
        # 이미 불러왔다면
        if called is True:
            return

        print("인기차트 목록을 받는중 입니다.")

        if getattr(sys, 'frozen', False):
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            driver = selenium.webdriver.Chrome(chromedriver_path)
        else:
            driver = selenium.webdriver.Chrome()

        # 멜론에서 top 100 목록 가져오기
        driver.get("https://www.melon.com/chart/index.htm")
        songs = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr")))
        del songs[0]

        # song_list 초기화
        title_list.clear()
        singer_list.clear()
        play_list.clear()

        count = 0
        for song in songs:
            song_info = song.text.split("\n")
            title_list.append(song_info[0])
            singer_list.append(song_info[1])
            count += 1
            print(str(count) + ". " + song_info[0] + " - " + song_info[1])

        time.sleep(1)
        self.btn_refresh.click()
        driver.quit()
        called = True

        print("\n인기차트 목록을 모두 받았습니다.\n")


class Thread2(QThread):
    # parent = MainWidget을 상속 받음.

    def __init__(self, parent):
        super().__init__(parent)
        self.driver = None

    def run(self):

        if len(play_list) == 0:
            return

        print("\n크롬드라이버가 실행중입니다.")

        if getattr(sys, 'frozen', False):
            chromedriver_path = os.path.join(sys._MEIPASS, "chromedriver.exe")
            self.driver = selenium.webdriver.Chrome(chromedriver_path)

        else:
            self.driver = selenium.webdriver.Chrome()

        # 유튜브에서 노래 실행하기
        self.driver.get("https://www.youtube.com/")

        # 실행버튼을 누른후에는 리스트가 변경이 안되도록
        playing_list = []
        for song in play_list:
            playing_list.append(song)

        for song in playing_list:
            elem = self.driver.find_element_by_name("search_query")
            elem.clear()
            elem.send_keys(song)
            elem.send_keys(Keys.RETURN)

            # 내용이 뜰때까지 대기
            songs = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.XPATH,
                                                                                             "/html/body/ytd-app/div/ytd-page-manager/ytd-search/div[1]/"
                                                                                             "ytd-two-column-search-results-renderer/div/ytd-section-list-renderer/div[2]/"
                                                                                             "ytd-item-section-renderer/div[3]/ytd-video-renderer[1]/div[1]/div/div[1]/div/h3/a")))

            time.sleep(1.5)

            # 맨위의 동영상 클릭
            # songs[0].click()
            songs[0].send_keys('\ue009' + "\n")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            time.sleep(3)
            # 광고 넘기기 및 다음곡 재생
            count, time_current, time_duration = 0, "", ""
            while True:

                time.sleep(1)

                try:
                    time_current = self.driver.find_element_by_css_selector(".ytp-time-current").text
                    time_duration = self.driver.find_element_by_css_selector(".ytp-time-duration").text
                    # print(time_current, time_duration)
                except:
                    pass

                try:
                    self.driver.find_element_by_css_selector(".ytp-ad-skip-button.ytp-button").click()
                except:
                    if time_current == time_duration and time_current != "":
                        break
                    try:
                        if self.driver.find_element_by_xpath('//*[@title="다시보기"]'):
                            break
                    except:
                        pass
                    pass

        self.driver.quit()


class MyApp(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()

        self.btn_refresh = QPushButton('helper', self)
        self.btn_refresh.clicked.connect(self.refresh)

    def initUI(self):

        self.cb_list = []
        self.groupbox = QGroupBox('인기차트 100')
        self.boxlayout = QFormLayout()
        self.groupbox.setGeometry(10, 60, 300, 60)
        self.groupbox.setLayout(self.boxlayout)

        self.scroll = QScrollArea()
        self.scroll.setWidget(self.groupbox)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(430)
        self.scroll.setStyleSheet('background-color: None')

        self.layout = QVBoxLayout(self)

        self.btn_crawling = QPushButton('인기차트 목록 불러오기')
        self.btn_crawling.clicked.connect(self.click_btn_crawling)
        self.btn_crawling.setStyleSheet('background-color: None')

        self.btn_start = QPushButton('재생')
        self.btn_start.clicked.connect(self.click_btn_start)
        self.btn_start.setStyleSheet('background-color: None')

        self.layout.addWidget(self.btn_crawling)
        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.btn_start)

        self.show()

    def check_it(self, state):
        self.cb_all.blockSignals(True)
        self.cb_all.setChecked(Qt.Unchecked)
        self.cb_all.blockSignals(False)

        if state == Qt.Checked:
            play_list.append(dictionary[self.sender().text()])
        else:
            play_list.remove(dictionary[self.sender().text()])

    def check_all(self, state):
        if state == Qt.Checked:
            for checkbox in self.cb_list:
                checkbox.blockSignals(True)
                checkbox.setCheckState(state)
                checkbox.blockSignals(False)
                if checkbox.text() not in play_list:
                    play_list.append(dictionary[checkbox.text()])
        else:
            for checkbox in self.cb_list:
                checkbox.blockSignals(True)
                checkbox.setCheckState(state)
                checkbox.blockSignals(False)
                play_list.clear()
        # print(play_list)

    def click_btn_crawling(self):
        thread1 = Thread1(self)
        thread1.start()

    def click_btn_start(self):
        self.thread2 = Thread2(self)
        self.thread2.start()

    def refresh(self):
        for i in reversed(range(self.boxlayout.count())):
            self.boxlayout.itemAt(i).widget().setParent(None)

        self.cb_all = QCheckBox('전체선택', self)
        self.cb_all.stateChanged.connect(self.check_all)

        self.boxlayout.addRow(self.cb_all)

        for i in range(len(title_list)):
            title, singer = title_list[i], singer_list[i]
            title_format = ""
            if len(title) >= 33:
                title_format = title[:30] + ".."
            else:
                title_format = title
            dictionary[title_format] = title + " " + singer
            globals()['cb{}'.format(i)] = QCheckBox(title_format, self)
            globals()['cb{}'.format(i)].stateChanged.connect(self.check_it)
            self.cb_list.append(globals()['cb{}'.format(i)])

            lb = QLabel(singer)
            self.boxlayout.addRow(globals()['cb{}'.format(i)], lb)

    def closeEvent(self, event):

        reply = QMessageBox.question(self, 'Message', '종료 하시겠습니까?',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                self.thread2.driver.quit()
            except:
                pass
            try:
                self.thread3.driver.quit()
            except:
                pass
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    print("meltube-player가 실행중 입니다.")
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.setWindowIcon(QIcon("image/icon.ico"))
    ex.setGeometry(1400, 150, 460, 560)
    ex.setStyleSheet('background-color: #3CB371')
    ex.setWindowTitle('meltube player')
    # E6E6FA 3CB371 DDA0DD 8FBC8F 2E8B57
    sys.exit(app.exec_())

# pyinstaller -w -F --add-binary "C:\chromedriver.exe";"." --icon=image/icon.ico meltube-player.py
