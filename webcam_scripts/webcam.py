import sys
import threading
import cv2
import numpy as np
import uvicorn
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
)
from fastapi import FastAPI
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision, BaseOptions

# ustaw kamerę domyślną
deviceID = 0
apiID = cv2.CAP_ANY


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    change_tangible_signal = pyqtSignal(float)
    change_gestures_signal = pyqtSignal(str)

    def __init__(self, gestures, tangible, parent=None):
        # Uruchom wątek kamery z parametrami przekazanymi od "rodzica"
        QThread.__init__(self, parent)
        self.video = cv2.VideoCapture(deviceID, apiID)
        self.runFlag = True
        self.gestures = gestures
        self.tangible = tangible
        if tangible:  # jeśli wybrano sterowanie tangible to inicjowany jest model YOLOv8
            self.model = YOLO('yolov8n.pt')
        if gestures:
            # jeśli wybrano sterowanie gestami to inicjowany jest GestureRecognizer w trybie transmisjii wideo
            options = mp.tasks.vision.GestureRecognizerOptions(base_options=BaseOptions(
                model_asset_path='gesture_recognizer.task'),
                running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                result_callback=self.processGestures)
            self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def run(self):
        # Przetwarzanie obrazu z kamery klatka po klatce
        while self.runFlag:
            ret, frame = self.video.read()
            if ret:
                if self.tangible:
                    self.processTangible(frame, self.model)
                if self.gestures:
                    # Przekaż aktualny znacznik czasowy, zmień format obrazu do sRGB
                    timestamp = self.video.get(cv2.CAP_PROP_POS_MSEC)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                    self.recognizer.recognize_async(mp_image, int(timestamp))
            else:
                self.video.release() # zakończ wątek jeśli brak nowych klatek

    def end(self): # kończy przetwarzanie obrazu z kamery
        self.runFlag = False
        self.video.release()
        self.wait()

    def processTangible(self, frame, model):
        # Detekcja obiektu klasy 67 - telefonu i wizualizacja detekcji na ekranie
        results = model.predict(frame, classes=67, conf=0.4)[0] # predykcja modelu z pewnością (ang. confidence) 40%
        annotated_frame = results.plot() # zaznacz wykryty obszar na obrazie wyjściowym
        if results.boxes: # jeśli sieć zwróciła wykryty obszar obiektu
            coordinates = results.boxes[0].xyxy[0].numpy() # współrzędne wierzchołków obszaru detekcji
            width = results.orig_shape[1] # szerokość obrazu wejściowego (klatki filmu)
            center = (coordinates[2] + coordinates[0]) / 2 # znajdowana jest wartość x punktu środkowego wykrytego obszaru ((x1 + x2)/2 bo lewy górny róg obrazu ma współrzędne (0,0))
            position = (center / (width / 2)) - 1 # pozycja przeskalowana do skali <-1,1>
            position *= -1 # obraz z kamery jest lustrzanym odbiciem więc trzeba znaleźć odwrotność pozycji
        else:
            position = 0 # jeśli nie wykryto obiektu pozycja ustwiana jest na 0
        self.change_pixmap_signal.emit(annotated_frame) # zmień wyświetlany na ekranie obraz
        self.change_tangible_signal.emit(position) # zmień aktualną pozycję gracza

    def processGestures(self, result: mp.tasks.vision.GestureRecognizerResult, output_image: mp.Image,
                        timestamp_ms: int):
        # zmień wyświetlany obraz na nową klatkę
        self.change_pixmap_signal.emit(output_image.numpy_view())
        if result.gestures: # jeśli wykryto gesty
            gesture = result.gestures[0][0].category_name
            print('gesture recognition result: {}'.format(gesture))
            if gesture.__eq__("Victory"): # jeśli to gest wiktorii to ustaw kierunek na lewo
                self.change_gestures_signal.emit('Left')
            elif gesture.__eq__("Closed_Fist"): # jeśli gest zamkniętej pięści to ustaw kierunek na prawo
                self.change_gestures_signal.emit('Right')
            else: # jeśli inny gest to ustaw kierunek na stop
                self.change_gestures_signal.emit('Stop')
        else: # jeśli nie wykryto gestów to ustaw kierunek na stop
            self.change_gestures_signal.emit('Stop')

def convertCVtoQt(cvImg):
    # funkcja zmienia format klatki filmu na format możliwy do wyświetlenia
    rgb_image = cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    p = convert_to_Qt_format.scaled(1280, 720, Qt.AspectRatioMode.KeepAspectRatio)
    return QPixmap.fromImage(p)


class Gestures(QWidget):
    def __init__(self):
        super(Gestures, self).__init__()

        self._createServer() # utwórz serwer API

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle("Gesture controller")

        mainLayout = QVBoxLayout(self)

        self.videoPlayer = QLabel()
        self.videoPlayer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gray = QPixmap(1280, 720)
        gray.fill(QColor("darkGray"))
        self.videoPlayer.setPixmap(gray)
        mainLayout.addWidget(self.videoPlayer)

        # Inicjuje wątek wideo z parametrami dla gestów
        self.thread = VideoThread(gestures=True, tangible=False)
        self.thread.change_pixmap_signal.connect(self.updateImage)
        self.thread.change_gestures_signal.connect(self.setGesturesDirection)
        self.thread.start()

        self.direction = 'Stop' # aktualny kierunek to stop

    def updateImage(self, cvImg): # funkcja zmieniająca wyświetlaną klatkę obrazu
        qtImg = convertCVtoQt(cvImg)
        self.videoPlayer.setPixmap(qtImg)

    def closeEvent(self, event): # przy zamknięciu okna zakończ wątek
        self.thread.end()
        event.accept()

    def _createServer(self): # utwórz serwer FastAPI
        self.app = FastAPI()

        # ustawia endpoint dla gestów
        @self.app.get("/gestures")
        async def getGesturesDirection():
            return {"direction": self.direction} # format JSON wysyłanych danych o kierunku

        # uruchom serwer na danym porcie (host - domyślny localhost)
        self.server = threading.Thread(target=uvicorn.run, kwargs={"app": self.app, "port": 81})
        self.server.start()

    def setGesturesDirection(self, direction: str):
        # funkcja odświeżająca kierunek gracza
        self.direction = direction


class Tangible(QWidget):
    def __init__(self):
        super(Tangible, self).__init__()

        self._createServer() # utwórz serwer API

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle("Tangible controller")

        mainLayout = QVBoxLayout(self)

        self.videoPlayer = QLabel()
        self.videoPlayer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gray = QPixmap(1280, 720)
        gray.fill(QColor("darkGray"))
        self.videoPlayer.setPixmap(gray)
        mainLayout.addWidget(self.videoPlayer)

        # Inicjuje wątek wideo z parametrami dla tangible interface
        self.thread = VideoThread(gestures=False, tangible=True)
        self.thread.change_pixmap_signal.connect(self.updateImage)
        self.thread.change_tangible_signal.connect(self.setTangiblePosition)
        self.thread.start()

        self.position = 0 # ustawia pozycję wyjściową na 0

    def updateImage(self, cvImg): # funkcja zmieniająca wyświetlaną klatkę obrazu
        qtImg = convertCVtoQt(cvImg)
        self.videoPlayer.setPixmap(qtImg)

    def closeEvent(self, event):
        self.thread.end()
        event.accept()

    def _createServer(self):
        self.app = FastAPI()

        # ustawia endpoint dla tangible
        @self.app.get("/tangible")
        async def getTangiblePosition():
            return {"position": self.position} # format JSON wysyłanych danych o pozycji

        # uruchom serwer na danym porcie (host - domyślny localhost)
        self.server = threading.Thread(target=uvicorn.run, kwargs={"app": self.app, "port": 81})
        self.server.start()

    def setTangiblePosition(self, position: float):
        # funkcja odświeżająca pozycję gracza, jeśli 0 to nie zmieniaj pozycji gracza (dokładne 0 raczej nie wydarzy się naturalnie)
        if position == 0:
            return
        self.position = position

# Główne okno aplikacji, opcje wyboru sterowania
class Webcam(QWidget):
    def __init__(self):
        super().__init__()
        self.webcam = None

        self.setWindowTitle("Options")

        gesturesBtn = QPushButton("Gestures controls", self)
        gesturesBtn.setFixedSize(100, 50)
        gesturesBtn.clicked.connect(self.gesturesClicked)

        tangibleBtn = QPushButton("Tangible controls", self)
        tangibleBtn.setFixedSize(100, 50)
        tangibleBtn.clicked.connect(self.tangibleClicked)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(tangibleBtn)
        mainLayout.addWidget(gesturesBtn)
        self.setLayout(mainLayout)

    def gesturesClicked(self):
        self.webcam = Gestures()
        self.webcam.show()
        self.hide()

    def tangibleClicked(self):
        self.webcam = Tangible()
        self.webcam.show()
        self.hide()


if __name__ == "__main__":
    webcam = QApplication([])
    window = Webcam()
    window.show()
    sys.exit(webcam.exec())
