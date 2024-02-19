# This Python file uses the following encoding: utf-8
import os
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtTest import QTest
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtCore import QUrl
import kfn_reader
import kar_reader
import re
import time, datetime

class PlayWidget(QWidget):
    def __init__(self):
        super(PlayWidget, self).__init__()
        self.load_ui()
    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "play_widget.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        ui_play=loader.load(ui_file, self)
        ui_file.close()
        self.labels=[ui_play.label_1,ui_play.label_2,ui_play.label_3]

#--------------------------------------------------------------------------

class Queue(QWidget):
    def __init__(self):
        super(Queue, self).__init__()
        self.load_ui()
    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "queue.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        ui_queue=loader.load(ui_file, self)
        ui_file.close()

        self.listWidget=ui_queue.listWidget
        self.pushButton_up=ui_queue.pushButton_up
        self.pushButton_down=ui_queue.pushButton_down
        self.pushButton_del=ui_queue.pushButton_del

#--------------------------------------------------------------------------

class Widget(QWidget):
    def __init__(self):
        super(Widget, self).__init__()
        self.__path_to_files=[] #Инкапсулированный список путей к файлам
        self.__pathes=[]        #Инкапсулированный список названий треков
        self.__queue=[]         #Инкапсулированный список файлов в очереди
        self.__flag_status="Stop" #Флаг состояния
        self.load_ui()
        self.action_play_widget()

    def load_ui(self):
        loader = QUiLoader()
        path = os.fspath(Path(__file__).resolve().parent / "form.ui")
        ui_file = QFile(path)
        ui_file.open(QFile.ReadOnly)
        ui=loader.load(ui_file, self)
        ui_file.close()

        self.folderButton=ui.folderButton
        self.listWidget=ui.listWidget
        self.queueButton=ui.queueButton
        self.playButton=ui.playButton
        self.stopButton=ui.stopButton
        #self.pauseButton=ui.pauseButton
        self.horizontalSlider=ui.horizontalSlider
        self.horizontalSlider.setEnabled(False)
        self.lcdNumber_ml=ui.lcdNumber_ml
        self.lcdNumber_mr=ui.lcdNumber_mr
        self.lcdNumber_sl=ui.lcdNumber_sl
        self.lcdNumber_sr=ui.lcdNumber_sr
        self.label_song_name=ui.label_8
        self.action()
    def change_label_song_name(self,name_file):
        self.label_song_name.setText(name_file)
    def create_player(self,folder_file):
        self.player = QMediaPlayer()
        self.audio = QAudioOutput()
        self.player.setAudioOutput(self.audio)
        self.player.setSource(QUrl.fromLocalFile(folder_file))
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
    def position_changed(self, position):
        if(self.horizontalSlider.maximum() != self.player.duration()):
            self.horizontalSlider.setMaximum(self.player.duration())
        self.horizontalSlider.setValue(position)
        seconds = int((position/1000)%60)
        minutes = int((position/60000)%60)
        if seconds<10:
            self.lcdNumber_sl.display(0)
            self.lcdNumber_sr.display(seconds)
        else:
            sec=str(seconds)
            self.lcdNumber_sl.display(int(sec[0]))
            self.lcdNumber_sr.display(int(sec[1]))
        if minutes<10:
            self.lcdNumber_ml.display(0)
            self.lcdNumber_mr.display(minutes)
        else:
            min=str(minutes)
            self.lcdNumber_ml.display(int(min[0]))
            self.lcdNumber_mr.display(int(min[1]))
    def duration_changed(self, duration):
        self.horizontalSlider.setRange(0, duration)

    #Метод добавления файлов в инкапсулированный список путей к файлам и в QListWidget
    def set_path_to_files(self,mass):
        prom=[]
        for a in mass:
            self.__path_to_files.append(a)
            p=a.split("/")
            prom.append(p[len(p)-1])#[:-4])
        n=0
        while n<len(prom):
            self.listWidget.addItem(prom[n])
            self.__pathes.append(prom[n])
            n+=1

    #Обработка событий нажания на кнопки
    def action(self):
        self.folderButton.clicked.connect(self.event_folderButton)
        self.listWidget.itemDoubleClicked.connect(self.event_listWidget)
        self.queueButton.clicked.connect(self.event_queueButton)
        self.playButton.clicked.connect(self.event_playButton)
        self.stopButton.clicked.connect(self.event_stopButton)
        #self.pauseButton.clicked.connect(self.event_pauseButton)

    #Обработка формы показа текста
    def action_play_widget(self):
        self.pw=PlayWidget()
        self.pw.show()

    #Обработчик кнопки - воспроизвести
    def event_playButton(self):
        #self.pauseButton.setEnabled(True)
        '''if self.__flag_status=="Pause":
            self.__flag_status="Play"
            self.player.play()
        else:'''
        self.__flag_status="Play"
        self.action_play()
    #Отбработчик кнопки - стоп
    def event_stopButton(self):
        #self.pauseButton.setEnabled(False)
        self.__flag_status="Stop"
        self.player.stop()

    #Обработчик кнопки - пауза
    '''def event_pauseButton(self):
        self.__flag_status="Pause"
        self.player.pause()'''

    def action_play(self):
        while len(self.__queue)!=0:
            i=0
            while i<len(self.__pathes):
                if self.__queue[0]==self.__pathes[i]:
                    path=self.__path_to_files[i]
                    break
                i+=1
            razresh=self.__queue[0].split(".")
            if razresh[len(razresh)-1]=="kfn":
                self.kfn_play(path)
            elif razresh[len(razresh)-1]=="mp3":
                self.mp3_play(path)
            elif razresh[len(razresh)-1]=="kar":
                self.kar_play(path)
            while self.player.mediaStatus() == self.player.MediaStatus.BufferedMedia:
                QTest.qWait(500)
            self.player.stop()
            self.__queue.pop(0)
            self.queueButton.setText(f"Queue {len(self.__queue)}")
    def mp3_play(self,path):
        self.create_player(path)
        self.change_label_song_name(self.__queue[0])
        self.pw.labels[0].setText("")
        self.pw.labels[1].setText("")
        self.pw.labels[2].setText("")
        self.player.play()
        self.__flag_status = "Play"
        QTest.qWait(1000)
        #while self.player.mediaStatus() == self.player.MediaStatus.BufferedMedia:
        #    QTest.qWait(500)
        #self.player.stop()
    def kfn_play(self,path):
        muz, head, sync, text_strings = kfn_reader.reader(path)
        self.create_player(f"./{muz}")
        self.player.play()
        self.__flag_status="Play"
        self.change_label_song_name(self.__queue[0])
        sync_c = [s for s in sync]
        start = 0
        i = 0
        while i < len(text_strings):
            if len(text_strings) >= (i + 3):
                t_s = [text_strings[i], text_strings[i + 1], text_strings[i + 2]]
            elif len(text_strings) >= (i + 2):
                t_s = [text_strings[i], text_strings[i + 1], ""]
            else:
                t_s = [text_strings[i], "", ""]
            self.pw.labels[0].setText(t_s[0].replace("/", ""))
            self.pw.labels[1].setText(t_s[1].replace("/", ""))
            self.pw.labels[2].setText(t_s[2].replace("/", ""))

            for cikl in range(3):
                if len(sync_c) < 1:
                    break
                n = 0
                t_s[cikl] = t_s[cikl].replace("  ", " ")
                words = re.split("[ /]", t_s[cikl])
                mask = []
                for s in t_s[cikl]:
                    if s == " ":
                        mask.append(1)
                    elif s == "/":
                        mask.append(5)
                mask.append(5)
                while n < len(words):
                    words_left = ""
                    words_right = ""
                    print(words[n])
                    sync_now = int(sync_c[0])
                    print(f"ожидание {sync_now - start}-{len(sync_c)} слово {words[n]}")
                    QTest.qWait((sync_now - start) * 10)
                    start = sync_now
                    sync_c.pop(0)
                    if n == len(words) - 1:
                        string = "<span style='color:yellow'>" + t_s[cikl].replace("/", "") + "</span>"
                    else:
                        l = 0
                        while l < len(words):
                            if l <= n:
                                if mask[l] == 1:
                                    words_left += words[l] + " "
                                elif mask[l] == 5:
                                    words_left += words[l]
                            else:
                                if mask[l] == 1:
                                    words_right += words[l] + " "
                                elif mask[l] == 5:
                                    words_right += words[l]
                            l += 1
                        string = "<span style='color:yellow'>" + words_left + "</span>" + words_right
                    self.pw.labels[cikl].setText(string)
                    '''while True:
                        if self.__flag_status == "Pause":
                            QTest.qWait(1000)
                        else:
                            break'''
                    n += 1
                    if self.__flag_status == "Stop":
                        return None
            i += 3
        #while self.player.mediaStatus() == self.player.MediaStatus.BufferedMedia:
        #    QTest.qWait(1000)
        #self.player.stop()
    def kar_play(self,path):
        m = kar_reader.midifile()
        m.load_file(path)
        start = datetime.datetime.now()
        dt = 0.
        self.create_player(path)
        self.change_label_song_name(self.__queue[0])
        self.pw.labels[0].setText("")
        self.pw.labels[1].setText("")
        self.pw.labels[2].setText("")
        self.player.play()
        self.__flag_status = "Play"
        while dt < max(m.kartimes) + 2:
            dt = (datetime.datetime.now() - start).total_seconds()
            m.update_karaoke(dt)

            #print('')
            #print(f't={dt} of {max(m.kartimes)}')
            iline=0
            while iline<3:
                string = "<span style='color:yellow'>" + m.karlinea[iline] + "</span>"+m.karlineb[iline]
                self.pw.labels[iline].setText(string)
                iline += 1
            #time.sleep(.1)
            QTest.qWait(1)
            '''while True:
                if self.__flag_status == "Pause":
                    QTest.qWait(1000)
                else:
                    break'''
            if self.__flag_status == "Stop":
                return None
    #Обработчик кнопки - открыть файлы
    def event_folderButton(self):
        res=QFileDialog.getOpenFileNames(self,"Открытие файла","./","KFN File(*.kfn);;MP3 File(*.mp3);;KAR File(*.kar)")
        if len(res[0])>0:
            self.set_path_to_files(res[0])

    #Обработчк QListWidget
    def event_listWidget(self,item):
        self.__queue.append(item.text())
        self.queueButton.setText(f"Queue {len(self.__queue)}")

    #Обработчик кнопки - очередь
    def event_queueButton(self):
        self.q=Queue()
        self.queue_listWidget=self.q.listWidget
        for n in range(len(self.__queue)):
            self.queue_listWidget.addItem(self.__queue[n])
        self.q.pushButton_up.clicked.connect(self.event_pushButton_up)
        self.q.pushButton_down.clicked.connect(self.event_pushButton_down)
        self.q.pushButton_del.clicked.connect(self.event_pushButton_del)
        self.q.show()
    def event_pushButton_up(self):
        row = self.queue_listWidget.currentRow()
        item = self.queue_listWidget.takeItem(row)
        self.queue_listWidget.insertItem(row - 1, item)
        self.queue_listWidget.setCurrentRow(row - 1)
        self.__queue.insert(row - 1, self.__queue.pop(row))
    def event_pushButton_down(self):
        row = self.queue_listWidget.currentRow()
        item = self.queue_listWidget.takeItem(row)
        self.queue_listWidget.insertItem(row + 1, item)
        self.queue_listWidget.setCurrentRow(row + 1)
        self.__queue.insert(row + 1, self.__queue.pop(row))
    def event_pushButton_del(self):
        ci=self.queue_listWidget.currentItem()
        cr=self.queue_listWidget.currentRow()
        self.queue_listWidget.takeItem(cr)
        #self.__queue.remove(ci.text())
        self.__queue.pop(cr)
        self.queueButton.setText(f"Queue {len(self.__queue)}")

#--------------------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication([])
    widget = Widget()
    widget.show()
    sys.exit(app.exec())
