import threading
import cv2
import uvicorn
from fastapi import FastAPI
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision, BaseOptions


def run():
    # iterating over every frame of the webcam footage
    while runFlag:
        ret, frame = video.read()
        if ret:
            # get current timestamp, format image and start recognition
            timestamp = video.get(cv2.CAP_PROP_POS_MSEC)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            recognizer.recognize_async(mp_image, int(timestamp))
            # process frame with yolo network
            processTangible(frame)
        else:
            video.release()


def processGestures(result: mp.tasks.vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    global gesturesIsNew
    # if detected gestures change direction else 'stop'
    if result.gestures:
        gesture = result.gestures[0][0].category_name
        print('gesture recognition result: {}'.format(gesture))
        gesturesIsNew = True
        if gesture.__eq__("Victory"):
            setGesturesDirection('Left')
        elif gesture.__eq__("Closed_Fist"):
            setGesturesDirection('Right')
        else:
            setGesturesDirection('Stop')
    else:
        setGesturesDirection('Stop')
        gesturesIsNew = False


def processTangible(frame):
    global tangibleIsNew
    # detect object of given class and show on video
    results = model.predict(frame, classes=67, conf=0.4)[0]
    if results.boxes:
        coordinates = results.boxes[0].xyxy[0].numpy()
        width = results.orig_shape[1]
        center = (coordinates[2] + coordinates[0]) / 2
        pos = (center / (width / 2)) - 1
        pos *= -1
        tangibleIsNew = True
        # rescaling the coordinates, the only ones that matter are the x coordinates,
        # we want to find the center of prediction hence left + right /2,
        # then we offset the position by the half-width and scale it to < -1; 1>
        # then multiply by -1 so that when moving to the left the player will move left
        # otherwise return 0 - do not update position
    else:
        pos = 0
        tangibleIsNew = False
    # send updated frame and position
    setTangiblePosition(pos)


def _createServer():
    app = FastAPI()

    # endpoint where we put the updated position
    @app.get("/tangible")
    async def getTangiblePosition():
        return {"position": position, "isNew": tangibleIsNew}

    # endpoint where we put the updated direction
    @app.get("/gestures")
    async def getGesturesDirection():
        return {"direction": direction, "isNew": gesturesIsNew}

    # start fastapi server at given port
    server = threading.Thread(target=uvicorn.run, kwargs={"app": app, "port": 81})
    server.start()


def setTangiblePosition(pos: float):
    global position
    # updating position, if returned position is equal 0 then remain in previous position
    if pos == 0:
        return
    position = pos


def setGesturesDirection(dirc: str):
    global direction
    # updating position, if returned position is equal 0 then remain in previous position
    direction = dirc


if __name__ == "__main__":
    video = cv2.VideoCapture(0, 0)
    runFlag = True
    position = 0
    direction = 'Stop'
    gesturesIsNew = False
    tangibleIsNew = False
    model = YOLO('yolov8n.pt')

    options = mp.tasks.vision.GestureRecognizerOptions(base_options=BaseOptions(
        model_asset_path='gesture_recognizer.task'),
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=processGestures)
    recognizer = vision.GestureRecognizer.create_from_options(options)

    _createServer()
    run()
