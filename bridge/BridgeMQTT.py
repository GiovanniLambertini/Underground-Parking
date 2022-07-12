import serial
import serial.tools.list_ports
import numpy as np
import urllib.request
import time
import random
import requests

#pip install requests
# pip install pymqtt
import paho.mqtt.client as mqtt

PORT_NAME = 'COM5'                                        #COM Bluetooth
LOCATION_ID = 1
QOS = 2
BASE_TOPIC = 'iot/underground_smart_parking/'
AVAILABLE_SLOTS_TOPIC = BASE_TOPIC + 'available_slots/' + str(LOCATION_ID)
SLOT_STATE_TOPIC = BASE_TOPIC + 'slot_state/' + str(LOCATION_ID) + "/"             #iot/underground_smart_parking/slot_state/<locationID>/<Section>/<SlotID>
BARRIER_OPENING = BASE_TOPIC + 'barrier/'
API_CODE = 'http://127.0.0.1/checkcode'

INITIAL_CHAR = '*'
FINAL_CHAR = '#'


class Bridge():

    def setupSerial(self):
        # open serial port
        self.serial = None

        print("list of available ports: ")
        ports = serial.tools.list_ports.comports()
        self.portname=None
        for port in ports:
            print (port.device)
            print (port.description)
            if PORT_NAME in port.description:
                self.portname = port.device
        if self.portname == None:
            print ("Error connecting to bluetooth port!")
            quit()

        print ("connecting to " + self.portname)

        while self.serial == None:
            try:
                if self.portname is not None:
                    self.serial = serial.Serial(self.portname, 9600, timeout=0)
            except:
                self.serial = None

        # buffer interno dalla seriale
        self.inbuffer = []

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting...")
        self.clientMQTT.connect("broker.hivemq.com", 1883, 60)

        self.clientMQTT.loop_start()


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        self.clientMQTT.subscribe(AVAILABLE_SLOTS_TOPIC)
        self.clientMQTT.subscribe(BARRIER_OPENING + "#")


    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + msg.payload.decode("utf-8"))
        if AVAILABLE_SLOTS_TOPIC in msg.topic:
            availableSlots = int(msg.payload.decode("utf-8"))

            response = bytearray(b'\xff')
            response += (b'\x01')  # Pacchetto di tipo 1
            response += availableSlots.to_bytes(1, 'little')
            response += (b'\xfe')

            self.serial.write(response)

        if BARRIER_OPENING in msg.topic:
            if "1" in str(msg.payload):
                print("Authorized user, sending command to open barrier")

                response = bytearray(b'\xff')
                response += (b'\x00')  # Pacchetto di tipo 0

                if "enter" in msg.topic:
                    response += (b'\x01')  # 1 - Successo entrata
                else:
                    response += (b'\x02')  # 2 - Successo uscita

                response += (b'\xfe')

                self.serial.write(response)

            else:
                print("Error, user unauthorized or bad request")

                response = bytearray(b'\xff')
                response += (b'\x00')  # Pacchetto di tipo 0
                response += (b'\x00')  # Errore
                response += (b'\xfe')

                self.serial.write(response)


    def setup(self):
        self.setupSerial()
        self.setupMQTT()

    def loop(self):
        # Ciclo infinito per lettura dei dati che arrivano dai sensori, tramite bluetooth
        while (True):
            if not self.serial is None:                            # Se la seriale è disponibile

                if self.serial.in_waiting > 0:                     # Se ci sono dati disponibili sulla seriale
                    lastchar = self.serial.read(1)

                    if lastchar == b'\xfe':  # EOL
                        print("\nValue received")
                        self.useData()
                        self.inbuffer = []
                    else:
                        self.inbuffer.append(lastchar)          # Aggiungo il dato al buffer

    def useData(self):
        # Ho ricevuto un pacchetto intero dalla porta seriale
        if len(self.inbuffer)<3:                                # Ho ricevuto almeno header, type, footer
            return False

        if self.inbuffer[0] != b'\xff':                         # Non ho ricevuto il byte di inizio
            return False

        if self.inbuffer[1] == b'\x00':
            code = bytearray();
            for i in range(2,9):
                code += self.inbuffer[i]

            code = code.decode("utf-8")

            print(code)

            body = requests.post(API_CODE, json={"type":"device", "locationId": str(LOCATION_ID), "code" : code})

            if body.status_code == 200:
                print("successfully received response")
                print(body.json())

            else:
                print("Error " + str(body.status_code))

        elif self.inbuffer[1] == b'\x01':

            section = self.inbuffer[2].decode("utf-8")
            slotId = int.from_bytes(self.inbuffer[3], byteorder='little')
            value = int.from_bytes(self.inbuffer[4], byteorder='little')                                # 0 libero, 1 occupato
            print(SLOT_STATE_TOPIC + str(section) + '/' + str(slotId))
            self.clientMQTT.publish(SLOT_STATE_TOPIC + str(section) + '/' + str(slotId), '{:d}'.format(value), qos=QOS, retain=True)

if __name__ == '__main__':
    br=Bridge()
    br.setup()
    br.loop()

