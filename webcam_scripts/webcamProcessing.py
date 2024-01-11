import threading
import cv2
import uvicorn
from fastapi import FastAPI
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision, BaseOptions


def run():
    # Przetwarzanie obrazu z kamery klatka po klatce
    while runFlag:
        ret, frame = video.read()
        if ret:
            # Znajdź aktualny znacznik czasowy, zmień format obrazu do sRGB i rozpocznij rozpoznawanie gestów
            timestamp = video.get(cv2.CAP_PROP_POS_MSEC)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            recognizer.recognize_async(mp_image, int(timestamp)) # działa asynchronicznie, wywołuje funkcję processGestures jako callback

            processTangible(frame) # przetwarzanie za pomocą sieci YOLOv8
        else:
            video.release()


def processGestures(result: mp.tasks.vision.GestureRecognizerResult, output_image: mp.Image, timestamp_ms: int):
    global gesturesIsNew
    if result.gestures: # jeśli wykryto gesty
        gesture = result.gestures[0][0].category_name
        print('gesture recognition result: {}'.format(gesture))
        gesturesIsNew = True # ustaw nowość parametru na prawdę
        if gesture.__eq__("Victory"): # jeśli wykryto gest wiktorii to ustaw kierunek na lewo
            setGesturesDirection('Left')
        elif gesture.__eq__("Closed_Fist"): # jeśli wykryto gest zamkniętej pięści to ustaw kierunek na prawo
            setGesturesDirection('Right')
        else:
            setGesturesDirection('Stop') # jeśli wykryto inny gest to ustaw kierunek na stop
    else:
        setGesturesDirection('Stop') # jeśli nie wykryto gestów (lub gest jest nierozpoznawalny) to ustaw nowość parametru na fałsz i kierunek na stop
        gesturesIsNew = False


def processTangible(frame):
    global tangibleIsNew
    # Detekcja obiektu klasy 67 - telefonu
    results = model.predict(frame, classes=67, conf=0.4)[0] # predykcja modelu z pewnością (ang. confidence) 40%
    if results.boxes: # jeśli sieć zwróciła wykryty obszar obiektu
        coordinates = results.boxes[0].xyxy[0].numpy() # współrzędne wierzchołków obszaru detekcji
        width = results.orig_shape[1] # szerokość obrazu wejściowego (klatki filmu)
        center = (coordinates[2] + coordinates[0]) / 2 # znajdowana jest wartość x punktu środkowego wykrytego obszaru ((x1 + x2)/2 bo lewy górny róg obrazu ma współrzędne (0,0))
        pos = (center / (width / 2)) - 1 # pozycja przeskalowana do skali <-1,1>
        pos *= -1 # obraz z kamery jest lustrzanym odbiciem więc trzeba znaleźć odwrotność pozycji
        tangibleIsNew = True # nowość pomiaru ustawiana jest na prawdę
    else: # jeśli nie wykryto obiektu to nowość pomiaru ustawiana jest na fałsz i pozycja na 0
        pos = 0
        tangibleIsNew = False
    setTangiblePosition(pos)


def _createServer():
    app = FastAPI()

    # endpoint dla tangible interface
    @app.get("/tangible")
    async def getTangiblePosition():
        return {"position": position, "isNew": tangibleIsNew} # format JSON danych

    # endpoint dla gestów
    @app.get("/gestures")
    async def getGesturesDirection():
        return {"direction": direction, "isNew": gesturesIsNew} # format JSON danych

    # uruchamiany jest serwer na domyślnym hoście (localhost) i porcie 81 z powyższymi endpointami typu GET
    server = threading.Thread(target=uvicorn.run, kwargs={"app": app, "port": 81})
    server.start()


def setTangiblePosition(pos: float):
    global position
    # funkcja odświeżająca pozycje gracza, jeśli wynosi 0 to nie zmieniaj pozycji (uzyskanie wartości dokładnie 0 jest bardzo mało prawdopodobne, jeśli jest 0 to zakładamy brak detekcji)
    if pos == 0:
        return
    position = pos


def setGesturesDirection(dirc: str):
    global direction
    # funkcja odświeżająca kierunek gracza
    direction = dirc


if __name__ == "__main__":
    video = cv2.VideoCapture(0, 0) # ustaw kamerę na domyślną
    runFlag = True
    position = 0 # wyjściowa pozycja ustawiana na 0
    direction = 'Stop' # wyjściowy kierunek ustawiony na stop
    gesturesIsNew = False # nowość parametrów jest fałsz
    tangibleIsNew = False
    model = YOLO('yolov8n.pt') # inicjowany model YOLOv8

    # inicjowany GestureRecognizer w trybie transmisji wideo, callback ustawiany na funkcję processGestures
    options = mp.tasks.vision.GestureRecognizerOptions(base_options=BaseOptions(
        model_asset_path='gesture_recognizer.task'),
        running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
        result_callback=processGestures)
    recognizer = vision.GestureRecognizer.create_from_options(options)

    _createServer() # uruchamiany serwer API
    run() # rozpoczynana jest pętla przetwarzania obrazu z kamery
