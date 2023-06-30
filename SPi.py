# Código para comunicarse desde la raspberrypi hasta la placa RFID
import spidev
import RPi.GPIO as GPIO
import time 

bus = 0
device = 0
speed_hz = 5000

PIN_INTERRUPCION = 6
PIN_NCS = 5
PIN_ENABLE = 13

# Para leer se tiene que poner 01 delante del registro para leer
# Para escribir se tiene que poner 00 delante del registro para leer
# Se va a emplear una máscara con la que hacer 
mascara_transmitir = 63
mascara_recibir = 64

# Se configuran las variables iniciales

spi = spidev.SpiDev()
spi.open(bus, device)

spi.max_speed_hz = speed_hz
spi.mode = 0b01 # Se configura el modo del clock

print("Se ha arrancado el código para comunicar por SPI, los parámetros son:")
print("Bus {}".format(bus))
print("Dispositivo {}".format(device))
print("Velocidad: {}".format(speed_hz))


def leerRegistro(registro, bytes):
    # Se envia el registro que se quiere leer
    # Primero se le aplica la máscara para poner los dos bits más significativos a cero
    registro = mascara_transmitir|registro
    
    # Se hace el or para poner el segundo bit más significativo a 1
    registro = mascara_recibir&registro

    
    # Se itera en todos los bytes que se quieren recibir para añadirlo a una lista
    lista_send = [registro]
    for i in range(bytes):
        lista_send.append(0x00)
        
    # Se mandan todos los comandos
    resultado = spi.xfer2(lista_send)    
    
    # Se descarta el primero valor de la lista puesto que es basura que tenía el 
    resultado = resultado[1:]
    
    return resultado

def escribirRegistro(registro,valores):
    # Se envia el registro que se quiere leer
    # Primero se le aplica la máscara para poner los dos bits más significativos a cero
    registro = mascara_transmitir|registro
        
    # Se itera en todos los bytes que se quieren recibir para añadirlo a una lista
    lista_send = [registro]
    for i in range(len(valores)):
        lista_send.append(valores[i])
        
    # Se mandan todos los comandos
    spi.xfer2(lista_send)
    # Da igual lo que devuelva
    
def cerrarComunicacion():
    
    spi.close()
    
def encenderRFID():
    print("Se empieza a encender la placa")
    # Se establece el pin de NCS como low

    GPIO.output(PIN_NCS, GPIO.LOW)

    # Para encender la placa se tienen que modificar los siguientes registros:
    # 0x00
    # 0x01
    escribirRegistro(0x00,[0x07])
    print("Se ha escrito en el registo de enable")
    
    escribirRegistro(0x01,[0x00])
    print("Se ha escrito en el registo de protocolo")
    
def modificarGanancia():
    # Función para modificar la ganancia de la transmisión
    pass

def leerRFOK():
    resultado = leerRegistro(0x2A,1)
    resultado = resultado[0]

    recibido = resultado >> 2
    recibido = recibido &1
    print("RF ok {}".format(recibido))

def leerRSSI():
    # Funcióp para leer el nivel de señal recibida
    resultado = leerRegistro(0x2B,1)
    resultado = resultado[0]
    rssi_q = 0xF0 | resultado
    rssi_i = 0x0F | resultado

    print("El nivel de señal en cuadratura: {}".format(rssi_q))
    print("El nivel de señal en fase: {}".format(rssi_i))

def leerInterrupcion():
    # Cuando se recibe una interrupción, se tiene que procesar para ver si se trata de recepción
    resultado = leerRegistro(0x37,1)
    
    # Se aplican las máscaras necesarias
    recibido = 0x20| resultado[0]
    recibido = recibido >> 5
    
    print("Valor del registro recibido: {}".format(recibido))
    
    if recibido == 1:
        print("Se va a leer el dato")
        leerDato()
        
def leerDato():
    valores = leerRegistro(0x3F,24)
    print("Valores recibidos: {}".format(valores))
    
def comprobarOK():
    # Función para leer si la transmisión está Ok
    recibido = leerRegistro(0x2A,1)
    print(recibido)
    recibido= recibido[0]>>2
    ok = 0x01 & recibido
    
    print("Todo ok: {}".format(ok))
    return ok
    
if __name__ == '__main__':
    
    # Se establecen los pines 
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_INTERRUPCION, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(PIN_INTERRUPCION, GPIO.FALLING, callback=leerInterrupcion, bouncetime=200)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_NCS, GPIO.OUT)
    GPIO.output(PIN_NCS,GPIO.HIGH)

    # Se arranca el código
    # Se enciende el RFID
    encenderRFID()
    
    # Se comprueba que todo está ok
    todo_ok = comprobarOK()
    while todo_ok != 1:
        print("No está todo ok")
        
    print("La placa ha sido inicializada")
    while True:
        try:
            time.sleep(1)
            leerRSSI()
            time.sleep(1)
            leerRFOK()

        except KeyboardInterrupt:
            print("Se termina el código")
            break
    
    print("Se ha cerrado de código")
    cerrarComunicacion()