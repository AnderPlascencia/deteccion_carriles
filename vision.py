import numpy as np
import cv2
from math import hypot
import socket
import time


def switcher_keys(var):
    switcher = {
        119:"w",
        97:"a",
        115:"s",
        100:"d",
        113:"q"
    }
    return switcher.get(var,None)

#configuracion para utilizar como servidor
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address=("", 5005)
sock.bind(address)#host address en blano para esperar mensaje y vincular

avgValue=[]
#lineas dominantes de carril
max_right_line = None
max_left_line = None

#ROI para recortes
pts= np.array([[0, 450], [602, 430], [602, 250], [80, 250]])
puntos= np.array([[0, 340], [900, 340], [900, 100], [0, 100]])#sin recorte

#rango de valores de rojo en HSV
rojo_bajos1 = np.array([0,65,75], dtype=np.uint8)
rojo_altos1 = np.array([12, 255, 255], dtype=np.uint8)
rojo_bajos2 = np.array([240,65,75], dtype=np.uint8)
rojo_altos2 = np.array([256, 255, 255], dtype=np.uint8)

X=0
contador=10
mensaje = ""
v_max=50.0
#352

print("Esperando mensaje...")
data, addr = sock.recvfrom(7)
#print "received from ", addr
#print "mensaje recibido: ", data, " longitud de dato: ", len(data)
#print addr

#lectura de camara celular
cap = cv2.VideoCapture("rtsp://192.168.43.67:8554/live.sdp") #streaming
#cap=cv2.VideoCapture("carriles7.mp4")

while(True):
    start_time = time.time() 
    ret, frame = cap.read()
    if not ret:
    #condicional para que no despliegue error al no cargar frame 
        print("no lee video")
        cap = cv2.VideoCapture("rtsp://192.168.43.67:8554/live.sdp")
        #cap=cv2.VideoCapture("carriles7.mp4")
        continue
    else:
        #print('This image is:', type(frame), 'with dimesions:', frame.shape[1], frame.shape[0])


    #recorte de poligono
        croped= frame.copy()
        recorte=frame.copy()
        recorte_rojo=frame.copy()
        mask = np.zeros(croped.shape[:2], np.uint8)
        cv2.drawContours(mask, [puntos], -1, (255, 255, 255), -1, cv2.LINE_AA)
        mascara= np.zeros(recorte_rojo.shape[:2], np.int8)
        cv2.drawContours(mascara, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)
        #suavizado de imagen para evitar ruido
        rect_image=cv2.GaussianBlur(croped,(11, 11), 0)
        #cambio a escala degrises
        rect_image= cv2.cvtColor(rect_image, cv2.COLOR_BGR2GRAY)

    #detector de bordes
        edges= cv2.Canny(rect_image, 150 , 200, apertureSize=3)
        
    #definir kernel para mascara de rojos
        kernel = np.ones((1,1),np.uint8)
        
    ## (3) do bit-op
        masked=cv2.bitwise_and(croped, croped, mask=mask)
        dst = cv2.bitwise_and(edges, edges, mask=mask)
        lines = cv2.HoughLinesP(dst,1,np.pi/180,10, maxLineGap=50)
        mascara2=cv2.bitwise_and(recorte_rojo, recorte_rojo, mask=mascara)


    #cambio a HSV
        hsv = cv2.cvtColor(mascara2, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv, rojo_bajos1, rojo_altos1)
        mask2 = cv2.inRange(hsv, rojo_bajos2, rojo_altos2)
        mask3 = cv2.morphologyEx(mask1, cv2.MORPH_OPEN, kernel)
        mask4 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
        mask5 = cv2.add(mask3, mask4)

        maxsizeL=0
        maxsizeR=0
        """
        if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            size = math.hypot(x2-x1, y2-y1)
            slope = ((y2-y1)/(x2-x1))
            #print "slope: \t", slope, "size: \t",size
            if slope >=0:#derecha
            cv2.line(recorte,(x1, y1), (x2, y2),(0, 0,255, 0.9), 4)
            if(size>maxsizeR):
                max_right_line=(x1, y1, x2, y2)
                maxsizeR=size
            else:#izquierda
            cv2.line(recorte,(x1, y1), (x2, y2),(255, 0, 0), 4)
                if(size>maxsizeL):
                max_left_line=(x1, y1, x2, y2)
                maxsizeL=size
        """
        height, width = frame.shape[:2]
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                size = hypot(x2-x1, y2-y1)
                if x1 < width/2:#izquierda
                    cv2.line(recorte, (x1, y1),(x2, y2), (255, 255, 0),4)
                    if size>maxsizeL:
                        max_left_line=(x1, y1, x2, y2)
                        maxsizeL=size
                else:#derecha
                    cv2.line(recorte, (x1, y1),(x2, y2), (100, 0, 255),4)
                    if size>maxsizeR:
                        max_right_line=(x1, y1, x2, y2)
                        maxsizeR=size
        

    #dibujar linea derecha e izquierda
        if max_right_line is not None and max_left_line is not None:
            cv2.line(recorte,(max_right_line[0], max_right_line[1]), (max_right_line[2], max_right_line[3]),(244, 133, 63), 8)
            cv2.line(recorte,(max_left_line[0], max_left_line[1]), (max_left_line[2], max_left_line[3]),(83, 168, 52), 8)
            avgX= (max_right_line[2]+max_left_line[0])/2
            avgValue.append(avgX)
            if len(avgValue)>5:
                avgValue.pop(0)
                X = int(np.mean(avgValue))
        #print "length array", len(avgValue), "value", avgValue
        cv2.line(recorte, (X, height-100), (X, height-100), (0, 255, 255), 8)
        height, width = frame.shape[:2]
        cv2.line(recorte, (width/2, height-100),(width/2, height-100), (0, 0, 255),8)
        
        if X==width/2:
            mensaje = `str(int(v_max))+ " " + str(int(v_max))`
            print "mensaje", mensaje
        else:
            diferencia=X-width/2    

        v_min =int(round((1.0-(abs(diferencia)/70.0))*v_max, 0))
        if v_min<20:
            v_min=20
        #print "vmin", v_min , "diferencia", diferencia

        missing = 3-len(str(v_min))
     
        while(missing>0):
            v_min = '0'+str(v_min)
            missing-=1	

        if diferencia>0:
            mensaje=`str(v_min)+ " 0" +str(int(v_max))` 
        else: 
            mensaje=`"0"+str(int(v_max))+" "+str(v_min)`

        #print "mensaje" , mensaje
        contador+=1
        #print `contador%100`+ mensaje
        
        key=switcher_keys(cv2.waitKey(1))
        if key is not None:
            print (key)
            if key == "q":
                break
        
        contador=10 if contador==99 else contador
        sock.sendto(mensaje, addr)
        print mensaje
        cv2.imshow("original", recorte)


        #cv2.imshow("mascara rojos", mask5)
        #cv2.imshow("recorte para rojos", mascara2)
        cv2.imshow("Canny", dst)
        #cv2.imshow("croped", masked)
        
        
        #print("-----%s segundo de ejecuccion    ----" % (time.time()-start_time))

#socket.close() cerrar socket
cap.release()
cv2.destroyAllWindows()
