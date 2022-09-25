from flask import Flask, render_template,Response
import cv2
import numpy as np
from pytesseract import pytesseract
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
def captura ():  
    camera = cv2.VideoCapture(0)    #crear instancia de video , 0 para abrir la camara principal, 1 para abrir una segunda camara
    while True:
        ret,image = camera.read() #Comienza a leer, camera.read devuelve el valor booleano (Verdadero/Falso). Devolverá Verdadero, si el marco se lee correctamente.
        if ret:
            gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
            gray=cv2.GaussianBlur(gray,(3,3),0)
            edged=cv2.Canny(gray,50,150) 
            kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
            closed=cv2.morphologyEx(edged,cv2.MORPH_CLOSE,kernel,iterations=2)   
            a,b,anc,alt =35,35,586,385
            cv2.rectangle(image, (a,b), (a+anc,b+alt), (0,0,255), 2)       #dibujar rectangulo de guía con dimensión esspectral de la identificación mexicana 
            cnts,_ = cv2.findContours(closed.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            area_detec = 0 
            for c in cnts :
                area = cv2.contourArea(c)
                peri=cv2.arcLength(c,True)
                approx=cv2.approxPolyDP(c,0.05*peri,True)
                if len(approx) == 4 and area > 200000: #area spectral
                    cv2.drawContours(image,[c],0,(0,255,0),3, cv2.LINE_AA)
                    area_detec = area
            (flag, encodedImage) = cv2.imencode(".jpg",image) #codifica formatos de imagen en datos de transmisión
            if not flag:
                continue
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n') #facilita la transmisión de red
            if area_detec > 220000:
                guardarINE(image)              
                break
    camera.release() #cerrar el video
    

def guardarINE(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray,(5,5),0)
    ocr(blurred)
   
def ocr(blurred):                       #sistema de reconocimiento de caracteres óptico 
    path_to_tesseract = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    pytesseract.tesseract_cmd = path_to_tesseract    
    text = pytesseract.image_to_string(blurred,lang='spa')
    try: 
        datos = text 
        cic_sp = datos.split("MEX")[1]
        cic = cic_sp.split("<")[0]
        cic = cic[:-1]
    
        ic_sp = datos.split("<<")[1]
        ic = ic_sp[4:13]
    
        ocr_sp = ic_sp
        ocr = ocr_sp[:13]
    
        datos_ine = {
        "cic" : cic,
        "identificadorCiudadano" : ic,
        "OCR" : ocr
        }    
        print(datos_ine)
        socketio.emit('datos',datos_ine, broadcast = True)
        socketio.emit('mensaje',"Verificación exitosa", broadcast = True)
    except:
        socketio.emit('error',"Actualizar la página y capturar el INE nuevamente", broadcast = True)

#........INICIA.............#
@app.route("/")
def index ():
    return render_template("index.html")

#..CAPTURA()..#

@app.route("/video")
def video():    
    return Response(captura(),mimetype='multipart/x-mixed-replace; boundary=frame')  # llevar el video a html  


if __name__ == "__main__":
    app.run(debug=True , port = 5000) 
