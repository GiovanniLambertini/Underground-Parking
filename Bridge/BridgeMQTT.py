import serial
import serial.tools.list_ports
import numpy as np
import urllib.request
import time

# pip install pymqtt
import paho.mqtt.client as mqtt

PORT_NAME = 'COM7'                                        #COM Bluetooth

class Bridge():


    def setupSerial(self):
        # open serial port
        self.ser = None
        print("list of available ports: ")

        ports = serial.tools.list_ports.comports()
        self.portname=None
        for port in ports:
            print (port.device)
            print (port.description)
            if PORT_NAME in port.description:
                self.portname = port.device
        print ("connecting to " + self.portname)

        try:
            if self.portname is not None:
                self.serial = serial.Serial(self.portname, 9600, timeout=0)
        except:
            self.serial = None

        # self.ser.open()

        # internal input buffer from serial
        self.inbuffer = []

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting...")
        self.clientMQTT.connect("127.0.0.1", 1883, 60)

        self.clientMQTT.loop_start()



    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.clientMQTT.subscribe("light")




    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic=='light':
            self.ser.write (msg.payload)

    def setup(self):
        self.setupSerial()
        #self.setupMQTT()

    def loop(self):
        # Ciclo infinito per lettura dei dati che arrivano dai sensori, tramite bluetooth
        while (True):

            if not self.ser is None:                            # Se la seriale è disponibile

                if self.ser.in_waiting > 0:                     # Se ci sono dati disponibili sulla seriale
                    lastchar = self.ser.read(1)

                    if lastchar == b'\xfe':  # EOL
                        print("\nValue received")
                        self.useData()
                        self.inbuffer = []
                    else:
                        self.inbuffer.append(lastchar)          # Aggiungo il dato al buffer

    def useData(self):
        # Ho ricevuto un pacchetto intero dalla porta seriale
        if len(self.inbuffer)<3:                                # Ho ricevuto almeno header, size, footer
            return False

        if self.inbuffer[0] != b'\xff':                         # Non ho ricevuto il byte di inizio
            return False

        numval = int.from_bytes(self.inbuffer[1], byteorder='little')
        for i in range (numval):
            val = int.from_bytes(self.inbuffer[i+2], byteorder='little')
            strval = "Sensor %d: %d " % (i, val)
            print(strval)
            self.clientMQTT.publish('sensor/{:d}'.format(i),'{:d}'.format(val))






if __name__ == '__main__':
    br=Bridge()
    br.setup()
    br.loop()

