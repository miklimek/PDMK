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

# Set camera
deviceID = 0  # 0 = open default camera
apiID = cv2.CAP_ANY  # 0 = autodetect default API


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    change_tangible_signal = pyqtSignal(float)
    change_gestures_signal = pyqtSignal(str)

    def __init__(self, gestures, tangible, parent=None):
        # initialize thread, set parameters based off parent's
        QThread.__init__(self, parent)
        self.video = cv2.VideoCapture(deviceID, apiID)
        self.runFlag = True
        self.gestures = gestures
        self.tangible = tangible
        if tangible:  # use yolo model if tangible
            self.model = YOLO('yolov8n.pt')
        if gestures:
            # set model to default and running mode to stream, after processing image call processGestures
            options = mp.tasks.vision.GestureRecognizerOptions(base_options=BaseOptions(
                model_asset_path='gesture_recognizer.task'),
                running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
                result_callback=self.processGestures)
            self.recognizer = vision.GestureRecognizer.create_from_options(options)

    def run(self):
        # iterating over every frame of the webcam footage
        while self.runFlag:
            ret, frame = self.video.read()
            if ret:
                if self.tangible:
                    self.processTangible(frame, self.model)
                if self.gestures:
                    # get current timestamp, format image and start recognition
                    timestamp = self.video.get(cv2.CAP_PROP_POS_MSEC)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                    self.recognizer.recognize_async(mp_image, int(timestamp))
            else:
                self.video.release()

    def end(self):
        self.runFlag = False
        self.video.release()
        self.wait()

    def processTangible(self, frame, model):
        # detect object of given class and show on video
        ## 11 - stop sign, 0 - person, 15 - cat, 67 - cell phone
        results = model.predict(frame, classes=67, conf=0.4)[0]
        annotated_frame = results.plot()
        if results.boxes:
            coordinates = results.boxes[0].xyxy[0].numpy()
            width = results.orig_shape[1]
            center = (coordinates[2] + coordinates[0]) / 2
            position = (center / (width / 2)) - 1
            position *= -1
            # rescaling the coordinates, the only ones that matter are the x coordinates,
            # we want to find the center of prediction hence left + right /2,
            # then we offset the position by the half-width and scale it to < -1; 1>
            # then multiply by -1 so that when moving to the left the player will move left
            # otherwise return 0 - do not update position
        else:
            position = 0
        self.change_pixmap_signal.emit(annotated_frame)
        self.change_tangible_signal.emit(position)
        # send updated frame and position

    def processGestures(self, result: mp.tasks.vision.GestureRecognizerResult, output_image: mp.Image,
                        timestamp_ms: int):
        # update video to newest frame
        self.change_pixmap_signal.emit(output_image.numpy_view())
        # if detected gestures change gesture else 'None'
        if result.gestures:
            gesture = result.gestures[0][0].category_name
            print('gesture recognition result: {}'.format(gesture))
            if gesture.__eq__("Victory"):
                self.change_gestures_signal.emit('Left')
            elif gesture.__eq__("Closed_Fist"):
                self.change_gestures_signal.emit('Right')
            else:
                self.change_gestures_signal.emit('Stop')
        else:
            self.change_gestures_signal.emit('Stop')

def convertCVtoQt(cvImg):
    # Convert from an opencv image to QPixmap
    rgb_image = cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_image.shape
    bytes_per_line = ch * w
    convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    p = convert_to_Qt_format.scaled(1280, 720, Qt.AspectRatioMode.KeepAspectRatio)
    return QPixmap.fromImage(p)


class Gestures(QWidget):
    def __init__(self):
        super(Gestures, self).__init__()

        self._createServer()

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle("Gesture controller")

        mainLayout = QVBoxLayout(self)

        self.videoPlayer = QLabel()
        self.videoPlayer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gray = QPixmap(1280, 720)
        gray.fill(QColor("darkGray"))
        self.videoPlayer.setPixmap(gray)
        mainLayout.addWidget(self.videoPlayer)

        # Start video thread, image processing within the thread
        self.thread = VideoThread(gestures=True, tangible=False)
        self.thread.change_pixmap_signal.connect(self.updateImage)
        self.thread.change_gestures_signal.connect(self.setGesturesDirection)
        self.thread.start()

        self.direction = 'Stop'

    def updateImage(self, cvImg):
        qtImg = convertCVtoQt(cvImg)
        self.videoPlayer.setPixmap(qtImg)

    def closeEvent(self, event):
        self.thread.end()
        event.accept()

    def _createServer(self):
        self.app = FastAPI()

        # endpoint where we put the updated position
        @self.app.get("/gestures")
        async def getGesturesDirection():
            return {"direction": self.direction}

        # start fastapi server at given port
        self.server = threading.Thread(target=uvicorn.run, kwargs={"app": self.app, "port": 81})
        self.server.start()

    def setGesturesDirection(self, direction: str):
        # updating position, if returned position is equal 0 then remain in previous position
        self.direction = direction


class Tangible(QWidget):
    def __init__(self):
        super(Tangible, self).__init__()

        self._createServer()

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle("Tangible controller")

        mainLayout = QVBoxLayout(self)

        self.videoPlayer = QLabel()
        self.videoPlayer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gray = QPixmap(1280, 720)
        gray.fill(QColor("darkGray"))
        self.videoPlayer.setPixmap(gray)
        mainLayout.addWidget(self.videoPlayer)

        # Start video thread, image processing within the thread
        self.thread = VideoThread(gestures=False, tangible=True)
        self.thread.change_pixmap_signal.connect(self.updateImage)
        self.thread.change_tangible_signal.connect(self.setTangiblePosition)
        self.thread.start()

        self.position = 0

    def updateImage(self, cvImg):
        qtImg = convertCVtoQt(cvImg)
        self.videoPlayer.setPixmap(qtImg)

    def closeEvent(self, event):
        self.thread.end()
        event.accept()

    def _createServer(self):
        self.app = FastAPI()

        # endpoint where we put the updated position
        @self.app.get("/tangible")
        async def getTangiblePosition():
            return {"position": self.position}

        # start fastapi server at given port
        self.server = threading.Thread(target=uvicorn.run, kwargs={"app": self.app, "port": 81})
        self.server.start()

    def setTangiblePosition(self, position: float):
        # updating position, if returned position is equal 0 then remain in previous position
        if position == 0:
            return
        self.position = position

# Main window, option to choose gesture controls or tangible controls
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
