# ____________________________________________________________________________                                                                       
#     ____________________     __          __       ___   ____ ___   ____ 
#    /  _/  _/ ____/ ____/    / /   ____ _/ /_     |__ \ / __ \__ \ / __ \
#    / / / // __/ / __/      / /   / __ `/ __ \    __/ // / / /_/ // / / /
#  _/ /_/ // /___/ /___     / /___/ /_/ / /_/ /   / __// /_/ / __// /_/ / 
# /___/___/_____/_____/    /_____/\__,_/_.___/   /____/\____/____/\____/  
# ____________________________________________________________________________                                                                       
# run.py
# Autor: Daniela Rojas
# Crea un servidor web donde se pueden ver los datos y el estado en tiempo real.
# ____________________________________________________________________________                                                                       
#

import numpy as np
from flask import Flask, request, render_template, json, Response
import time
import socket
import threading
import os
from joblib import dump, load


app = Flask(__name__)

global LISTA_NOMBRE_ACTIVIDADES
global LISTA_LINKS_ACTIVIDADES

LISTA_NOMBRE_ACTIVIDADES = ['Nombre_0', 'Nombre_1', 'Nombre_2', 'Nombre_3', 'Nombre_4', 'Nombre_5', 'Nombre_6']
LISTA_LINKS_ACTIVIDADES = ['Actividad_0.png', 'Actividad_1.png', 'Actividad_2.png', 'Actividad_3.png', 'Actividad_4.png', 'Actividad_5.png', 'Actividad_6.png']

NOMBRE_GRUPO = "Introducción IEE"

COLOR_TITULO = "cadetblue"
COLOR_FONDO = "#c7ddde"

######\\\###########\\\#########\\\#########\\\###########\\\########\\\#####
######\\\###########\\\#########\\\#########\\\###########\\\########\\\#####
######\\\###########\\\#########\\\#########\\\###########\\\########\\\#####
tiempoMLC = "0.5s"
global GUARDAR
GUARDAR = False
global numeroAnimalMobile
numeroAnimalMobile = 1
global NUMERO_MAXIMO_MODULOS
NUMERO_MAXIMO_MODULOS = 1

global ESTADO_MODULOS
ESTADO_MODULOS = []

global ACTIVIDAD_ACTUAL
global datosCompletos 
global datosTemporales 
ACTIVIDAD_ACTUAL = [] ## una actividad para cada dispositivo
datosCompletos =[]
datosTemporales =[]
global tiemposEstadisticosTotales 
global tiempo_inicio_por_modulo 
global tiempo_ultima_actualizacion_por_modulo
global tamañoDatosTemporales
tiemposEstadisticosTotales = []
tiempo_ultima_actualizacion_por_modulo = []
tiempo_inicio_por_modulo = []
for modulo in  range(0,NUMERO_MAXIMO_MODULOS):
	ACTIVIDAD_ACTUAL.append(3)
	ESTADO_MODULOS.append(0)
	datosCompletos.append(  ['','','','','','','','','',''] )
	tiemposEstadisticosTotales.append( [ 0.000, 0.000 , 0.000 , 0.000, 0.000,0.000, 0.000 ])
	tiempo_ultima_actualizacion_por_modulo.append(time.time())
	tiempo_inicio_por_modulo.append('0')

datosTemporales = np.zeros((len(datosCompletos) , 1,6)).tolist()
tamañoDatosTemporales = np.zeros((NUMERO_MAXIMO_MODULOS, 1)).tolist()



lock = threading.Lock()

global TIEMPO_INICIO
TIEMPO_INICIO = time.time() #Variable que guarda el tiempo en el que el servidor empezó a correr
global fechaYhora
FECHA_Y_HORA = "" #Variable para etiquetar los datos con fechas y horas
global nuevaLineaDatos
nuevaLineaDatos = [0,0,0,0,0,0,0,0,0,""]

###SWITCH MLC
global estadoLEDMLC
estadoLEDMLC = 0


### hilo para recibir los datos por sockets
def ThreadActualizarSocket():
	global TIEMPO_INICIO
	global ACTIVIDAD_ACTUAL
	global datosCompletos 
	global datosTemporales 
	global nuevaLineaDatos
	global ESTADO_MODULOS
	global NUMERO_MAXIMO_MODULOS
	global tiempo_inicio_por_modulo
	print("ThreadActualizarSocket Started... ")
	UDP_IP = socket.gethostbyname(socket.gethostname())
	UDP_PORT = 9001 ## Este puerto debe coincidir con el configurado en el módulo wifi para el envío de datos
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((UDP_IP, UDP_PORT))
	print("____________________________________________")
	print("Puerto Abierto")
	print("____________________________________________")	


	while True:
		data, addr = s.recvfrom(1024)
		data = data.decode()
		try:
			ArrayData = data.split("#")
			Ax = float(ArrayData[0])
			Ay = float(ArrayData[1])
			Az = float(ArrayData[2])
			Gx = float(ArrayData[3])
			Gy = float(ArrayData[4])
			Gz = float(ArrayData[5])
			IdClient = int(ArrayData[6])-1
			NumeroPaquete = float(ArrayData[7])
			fechaYhora = str(time.strftime("%c"))

			nuevaLineaDatos = [ Ax,Ay,Az,Gx,Gy,Gz,IdClient,NumeroPaquete,ACTIVIDAD_ACTUAL[IdClient], fechaYhora]
			##print ("linea", nuevaLineaDatos)
			lock.acquire()
			datosCompletos[IdClient].append(nuevaLineaDatos)
			datosTemporales[IdClient].append(nuevaLineaDatos[0:6])
			lock.release()
			ESTADO_MODULOS[IdClient] = 1
			#print(time.time())
			tiempo_ultima_actualizacion_por_modulo[IdClient] = time.time()
			#print(tiempo_ultima_actualizacion_por_modulo)
			if ( tiempo_inicio_por_modulo[IdClient]== '0'):
				tiempo_inicio_por_modulo[IdClient] = time.ctime(time.time())
			if (GUARDAR):
				file = open("./results/data/data"+str(TIEMPO_INICIO)+".csv","a") #Se activa (crea) el archivo para guardar (escribir) un nuevo dato
				file.write( ( fechaYhora + ","+"	 %.1f,	 %.5f,	 %.5f,	 %.5f,	 %.5f,	 %.5f,	 %.5f,	 %.5f"%(NumeroPaquete, IdClient, Ax, Ay, Az, Gx, Gy, Gz) ) + ",	" + str(ACTIVIDAD_ACTUAL[IdClient]) + "	\n" )
				file.close() #Cada vez que el servidor recibe un dato lo guarda adecuamente en el archivo plano de texto
						  	 #para evitar perdidas de datos
		except Exception as e:
			print(e)
			print("Error en dato")
threading.Thread(target=ThreadActualizarSocket).start()

### hilo para realizar predición de estados
def ThreadMLC():
	global estadoLEDMLC
	global datosTemporales 
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	global ESTADO_MODULOS
	global tamañoDatosTemporales
	global tiemposEstadisticosTotales 
	global tiempo_ultima_actualizacion_por_modulo
	print("ThreadMLC Started ...")
	try:
		loaded_model = load('model.joblib').set_params(n_jobs=1) 
		print("Loaded model from disk")
	except Exception as inst:
	 	print("No se cargó el modelo")
	 	print(type(inst))    # la instancia de excepción
	 	print(inst.args)     # argumentos guardados en .args
	 	print(inst)          # __str__ permite imprimir args directamente,
	else:
	 	print("____________________________________________")
	 	print("MODELO CARGADO")
	 	print("____________________________________________")	


	while True:
		longitudTemporalModuloMayor=0
		for i in range(0,NUMERO_MAXIMO_MODULOS):
			x = len(datosTemporales[i])
			### guarda la longitud mayor para despues saber si hay datos suficientes para hacer la prediccion
			if (x>longitudTemporalModuloMayor):
				longitudTemporalModuloMayor=x
		CANTIDAD_DATOS = 3
		if(estadoLEDMLC==1):
			lock.acquire()
			if(longitudTemporalModuloMayor>= CANTIDAD_DATOS):
				for animali in range(0,NUMERO_MAXIMO_MODULOS):
					x = len(datosTemporales[animali])
					if (x>= CANTIDAD_DATOS): ### si no esta vacio 
						#print("Realizando predicción . . .")
						### se realiza la predicion
						inicio = time.time()
						datosPredecir = datosTemporales[animali]
						datosPredecir = np.array( [datosPredecir[len(datosPredecir)-CANTIDAD_DATOS:len(datosPredecir)] ])[0] ### Matriz 1 filas, 6 columnas
						#print(datosPredecir, datosPredecir.shape)
						#datosPredecir = datosPredecir.reshape(1,100,6,1)
						res = loaded_model.predict(datosPredecir)
						#print(time.time()-inicio)
						#print('res',res)
						predecida = np.bincount(res)
						#print('predecida', predecida)
						ACTIVIDAD_ACTUAL[animali]= int(np.argmax(predecida))
						#print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL)
				datosTemporales = np.zeros((len(datosCompletos) , 1,6)).tolist()
			lock.release()
		#print("esperar")
		#time.sleep(10)

threading.Thread(target=ThreadMLC).start()

@app.route('/')
def indexTemplate():
	#print("____________________________________________")
	#print(" Running ... ")
	#print("____________________________________________")	
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	global numeroAnimalMobile
	global LISTA_NOMBRE_ACTIVIDADES
	global LISTA_LINKS_ACTIVIDADES
	LISTA = zip(LISTA_NOMBRE_ACTIVIDADES, LISTA_LINKS_ACTIVIDADES, range(0,len(LISTA_NOMBRE_ACTIVIDADES)))
	LISTA_ACTIVIDADES_int= range(0,len(LISTA_NOMBRE_ACTIVIDADES))
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	return render_template( 'index.html' ,tiempoMLC=tiempoMLC, COLOR_TITULO=COLOR_TITULO, COLOR_FONDO=COLOR_FONDO, NOMBRE_GRUPO=NOMBRE_GRUPO,LISTA=LISTA, ListaModulos=ListaModulos,NUMERO_MAXIMO_MODULOS=NUMERO_MAXIMO_MODULOS  )


@app.route('/actualizar_estado', methods = ['POST'])
def actualizar_estado():
	global ACTIVIDAD_ACTUAL
	global NUMERO_MAXIMO_MODULOS
	for modulo in  range(0,NUMERO_MAXIMO_MODULOS): 
		ACTIVIDAD_ACTUAL[modulo] = int(request.form['estadoVaca'+str(modulo)])
	#print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL)
	##print("xxxxxxxxxxxxxxxxxxx")
	##print('ACTIVIDAD_ACTUAL',ACTIVIDAD_ACTUAL )
	return ""

### Recibe la información del switch SAVE, para así GUARDAR DATOS
@app.route('/switchSAVE', methods = ['POST'])
def switchSAVE():
	global GUARDAR
	estadoLEDnuevo = request.form['led']
	#print("la nueva accion del LED es : "  + estadoLEDnuevo)
	if(estadoLEDnuevo=='true'):
		GUARDAR=True
	elif(estadoLEDnuevo=='false'):
		GUARDAR=False
	return ""

### Recibe la información del switch MLC, para así comenzar a predecir
@app.route('/switchMLC', methods = ['POST'])
def switchMLC():
	global estadoLEDMLC
	estadoLEDnuevo = request.form['led']
	#print("la nueva accion del LED es : "  + estadoLEDnuevo)
	if(estadoLEDnuevo=='true'):
		estadoLEDMLC=1
	elif(estadoLEDnuevo=='false'):
		estadoLEDMLC=0
	return ""


### Envia la información de los estados de conexion de los modulos
@app.route('/actualizarEstadoModulos', methods=['POST'])
def actualizarEstadoModulos():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global ESTADO_MODULOS
	global datosTemporales
	global tiempo_ultima_actualizacion_por_modulo
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	tiempoDesconectado = 2
	for modulo in ListaModulos:
		#print(tiempo_ultima_actualizacion_por_modulo[modulo])
		#print('tiempo_ultima_actualizacion_por_modulo',time.time()-tiempo_ultima_actualizacion_por_modulo[modulo])
		if(time.time()-tiempo_ultima_actualizacion_por_modulo[modulo]>=tiempoDesconectado):
			ESTADO_MODULOS[modulo] = 0

	return json.dumps({'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS,'ESTADO_MODULOS':ESTADO_MODULOS, 'ListaModulos':list(ListaModulos)});

### Envia la información de las graficas.
@app.route('/actualizarGraficas', methods=['POST'])
def actualizarGraficas():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global TIEMPO_INICIO
	global nuevaLineaDatos ##[ Ax,Ay,Az,Gx,Gy,Gz,IdClient,NumeroPaquete,ACTIVIDAD_ACTUAL[IdClient], fechaYhora]
	modulo = int(nuevaLineaDatos[6])
	Ax = nuevaLineaDatos[0]
	Ay = nuevaLineaDatos[1]
	Az = nuevaLineaDatos[2]
	Gx = nuevaLineaDatos[3]
	Gy = nuevaLineaDatos[4]
	Gz = nuevaLineaDatos[5]
	tiempo = time.time()-TIEMPO_INICIO
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	return json.dumps({'Ax':Ax ,'Ay':Ay ,'Az':Az ,'Gx':Gx ,'Gy':Gy ,'Gz':Gz ,'tiempo':tiempo, 'modulo':modulo,'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS, 'ListaModulos':list(ListaModulos), 'nuevaLineaDatos':nuevaLineaDatos});

def calcularTiempos():
	global NUMERO_MAXIMO_MODULOS
	global ACTIVIDAD_ACTUAL
	global tiemposEstadisticosTotales 
	global tiempo_inicio_por_modulo 
	global tiempo_ultima_actualizacion_por_modulo
	global ESTADO_MODULOS
	nptiempoEstadisticos = np.array(tiemposEstadisticosTotales)
	for modulo_i in range(0,NUMERO_MAXIMO_MODULOS):
		tiempoActual = time.time()
		if not (ESTADO_MODULOS[modulo_i] == 0):
			tiempoTranscurridoHoras = (((tiempoActual - tiempo_ultima_actualizacion_por_modulo[modulo_i])/3600))
			nptiempoEstadisticos[int(modulo_i),int(ACTIVIDAD_ACTUAL[modulo_i])] = (tiempoTranscurridoHoras +  nptiempoEstadisticos[int(modulo_i),int(ACTIVIDAD_ACTUAL[modulo_i])])
		#tiempo_ultima_actualizacion_por_modulo[modulo_i] = tiempoActual
	tiemposEstadisticosTotales = nptiempoEstadisticos.tolist()
### Envia la información de los estados de los animales
@app.route('/actualizarEstadosInterfaz', methods=['POST'])
def actualizarEstadosInterfaz():
	#enviar información al cliente
	global NUMERO_MAXIMO_MODULOS
	global ACTIVIDAD_ACTUAL
	global tiemposEstadisticosTotales 
	global tiempo_inicio_por_modulo 
	calcularTiempos()
	nptiempoEstadisticos = np.array(tiemposEstadisticosTotales)
	tiemposComer = [ '%.2f' % elem for elem in nptiempoEstadisticos[:,0].tolist() ]
	tiemposRumia = [ '%.2f' % elem for elem in nptiempoEstadisticos[:,1].tolist() ]
	tiemposCaminar = [ '%.2f' % elem for elem in nptiempoEstadisticos[:,2].tolist() ]
	tiemposNada = [ '%.2f' % elem for elem in nptiempoEstadisticos[:,3].tolist() ]
	ListaModulos = range(0, len(ACTIVIDAD_ACTUAL))
	np.savetxt("./resultados/tiemposEstadisticosTotales", tiemposEstadisticosTotales, newline=" \n ")
	#print("tiempos",tiemposComer,tiemposRumia,tiemposCaminar,tiemposNada)
	global LISTA_NOMBRE_ACTIVIDADES
	global LISTA_LINKS_ACTIVIDADES
	maximoActividades = len(LISTA_NOMBRE_ACTIVIDADES)
	return json.dumps({'maximoActividades':maximoActividades,'LISTA_LINKS_ACTIVIDADES':LISTA_LINKS_ACTIVIDADES,'LISTA_NOMBRE_ACTIVIDADES':LISTA_NOMBRE_ACTIVIDADES,'tiempo_inicio_por_modulo':tiempo_inicio_por_modulo,'tiemposNada':tiemposNada,'tiemposCaminar':tiemposCaminar,'tiemposRumia':tiemposRumia,'tiemposComer':tiemposComer,'ACTIVIDAD_ACTUAL':ACTIVIDAD_ACTUAL,'NUMERO_MAXIMO_MODULOS':NUMERO_MAXIMO_MODULOS, 'ListaModulos':list(ListaModulos)});

### Envia la información de los estados de los animales
@app.route('/actualizarEstadoROBOT')
def actualizarEstadoROBOT():
	#enviar información al ROBOT
	global ACTIVIDAD_ACTUAL
	estadoRobot = ACTIVIDAD_ACTUAL[0]
	#print('estadoRobot',estadoRobot)
	return json.dumps({ 'estadoRobot':estadoRobot});


if __name__ == '__main__':
	app.run(host='0.0.0.0',debug = False ,port= 9001, use_reloader=False, threaded=True)


# ____________________________________________________________________________                                                                       
# ______            _      _        ______      _           
# |  _  \          (_)    | |       | ___ \    (_)          
# | | | |__ _ _ __  _  ___| | __ _  | |_/ /___  _  __ _ ___ 
# | | | / _` | '_ \| |/ _ \ |/ _` | |    // _ \| |/ _` / __|
# | |/ / (_| | | | | |  __/ | (_| | | |\ \ (_) | | (_| \__ \
# |___/ \__,_|_| |_|_|\___|_|\__,_| \_| \_\___/| |\__,_|___/
#                                             _/ |          
#                                            |__/           
# ____________________________________________________________________________                                                                       
#

