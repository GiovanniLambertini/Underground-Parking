#pip install flask-sqlalchemy
#pip install pymysql

from flask import Flask
from config import Config
from flask import render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import dateutil
import random
import paho.mqtt.client as mqtt
import threading

appname = "IOT - sample1"
app = Flask(appname)
myconfig = Config
app.config.from_object(myconfig)

# db creationpip in
db = SQLAlchemy(app)

CODE_LENGTH=5
BOOKING_MINUTES = 60
PRICE_TOPIC = "iot/underground_smart_parking/price/"
SLOT_STATE_TOPIC = "iot/underground_smart_parking/slot_state/"
AVAILABLE_SLOTS_TOPIC = "iot/underground_smart_parking/available_slots/"
QOS = 2

currentPrice = []

class User(db.Model):
    userId = db.Column(db.Integer, primary_key = True)
    type = db.Column(db.String(3))                                                                          #car o app
    licensePlate = db.Column(db.String(10))

    def __init__(self, userId, type, licensePlate):
        self.userId = userId
        self.type = type
        self.licensePlate = licensePlate

class Parking(db.Model):
    locationId = db.Column(db.Integer, primary_key = True)
    locationName = db.Column(db.String(50))
    numSlots = db.Column(db.Integer)


    def __init__(self, locationId, locationName, numSlots):
        self.locationId = locationId
        self.locationName = locationName
        self.numSlots = numSlots


class AvailableSlots(db.Model):
    locationId = db.Column(db.Integer,  db.ForeignKey('parking.locationId'), primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, primary_key=True)
    numAvailableSlots = db.Column(db.Integer, primary_key=True)

    def __init__(self, numAvailableSlots, locationId):
        self.locationId = locationId
        self.numAvailableSlots = numAvailableSlots

class Slot(db.Model):
    slotId = db.Column(db.Integer, primary_key=True)
    slotSection = db.Column(db.String(2), primary_key=True)

    def __init__(self, slotId, slotSection):
        self.slotId = slotId
        self.slotSection = slotSection

class SlotAvailability(db.Model):
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    slotId = db.Column(db.Integer, db.ForeignKey('slot.slotId'), primary_key=True)
    slotSection = db.Column(db.String(2),  db.ForeignKey('slot.slotSection'), primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    isAvailable = db.Column(db.Boolean)

    def __init__(self, locationId, slotId, slotSection, isAvailable):
        self.locationId = locationId
        self.slotId = slotId
        self.slotSection = slotSection
        self.isAvailable = isAvailable

class Booking(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), primary_key=True)
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow, primary_key=True)
    code = db.Column(db.String(7))
    bookingStatus = db.Column(db.String(10), default="valid")

    def __init__(self, userId, locationId):
        self.userId = userId
        self.locationId = locationId

    def __init__(self, userId, locationId, code):
        self.userId = userId
        self.locationId = locationId
        self.code = code


class Parked(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), primary_key=True)
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    entranceTimestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)      #Entrance timestamp
    exitTimestamp = db.Column(db.DateTime(timezone=True), nullable=True)                                    #Exit timestamp
    pricePerHour = db.Column(db.Float)
    code = db.Column(db.String(7))

    def __init__(self, userId, locationId, pricePerHour, code):
        self.userId = userId
        self.locationId = locationId
        self.pricePerHour = pricePerHour
        self.code = code

class MQTTServer():

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting mqtt...")
        self.clientMQTT.connect("broker.emqx.io", 1883, 60)

        self.clientMQTT.loop_start()


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        self.clientMQTT.subscribe(PRICE_TOPIC)
        self.clientMQTT.subscribe(SLOT_STATE_TOPIC)


    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if PRICE_TOPIC in msg.topic:
            locationId = msg.topic.replace(PRICE_TOPIC, "")

            global currentPrice
            currentPrice[locationId] = float(msg.payload)

        elif SLOT_STATE_TOPIC in msg.topic:
            slot = msg.topic.replace(SLOT_STATE_TOPIC, "")
            locationId, slotSection, slotId = slot.split("/")

            if msg.payload == "1":
                isAvailable = True
            else:
                isAvailable = False

            slotAvailability = SlotAvailability(locationId, slotId, slotSection, isAvailable)
            db.session.add(slotAvailability)
            db.session.commit()


    def setup(self):
        self.setupMQTT()


@app.errorhandler(404)
def page_not_found(error):
    return 'Page not found', 404

@app.route('/')
def testoHTML():
    #if request.accept_mimetypes['application/json']:
    return jsonify( {'successful':True, 'second':'Gio'}), '200 OK'

@app.route('/prova', methods=['GET'])
def prova():
    elenco=User.query.order_by(User.userId.desc()).limit(10).all()

    string = ''
    for el in elenco:
        string += str(el.userId) + ', '

    return string

@app.route('/booking', methods=['POST'])
def bookParkSlot():
    body = request.get_json()

    if not 'type' in body or not 'userId' in body or not 'locationId' in body:
        return jsonify( {'successful':False, 'error':'Some mandatory fields are missing'}), '400 Bad Request'

    if body['type'] != 'car' and body['type'] != 'device':
        return jsonify( {'successful':False, 'error':'Type must be car or device'}), '400 Bad Request'
    if body['type'] == 'car':
        code = None

    else:
        repeat=True
        while (repeat):
            #Generate 5 digits code
            code = "*"
            for i in range(CODE_LENGTH):
                code += str(random.randint(0,9))
            code += "#"

            #Controllo che il codice non sia gia' in uso
            #now = dateutil.parser.parse(datetime.utcnow().isoformat())
            #booking_minutes_ago = now - timedelta(days=30)

            #usedCodes = db.session.query(Booking).filter(Booking.locationId == body['locationId'], Booking.timestamp >= booking_minutes_ago).with_entities(Booking.code).all()
            usedCodes = db.session.query(Booking).filter(Booking.locationId == body['locationId'], Booking.bookingStatus != 'expired', Booking.bookingStatus != 'used').with_entities(Booking.code).all()       # Codici in uso o ancora validi

            if (code, ) not in usedCodes:
                repeat = False

        previousAvailableSlots = db.session.query(AvailableSlots).filter(AvailableSlots.locationId == body['locationId']).order_by(AvailableSlots.timestamp.desc()).with_entities(AvailableSlots.numAvailableSlots).first()
        if previousAvailableSlots == None:
            previousAvailableSlots = db.session.query(Parking).filter(Parking.locationId == body['locationId']).with_entities(Parking.numSlots).first()

    if previousAvailableSlots == None:                                  #Prima prenotazione
        previousAvailableSlots = 6
    else:
        previousAvailableSlots = previousAvailableSlots[0]
    if previousAvailableSlots < 1:
        #previousAvailableSlots=6
        return jsonify({'successful': False, 'code': None}), '200 Full parking'

    booking = Booking(body['userId'], body['locationId'], code)
    db.session.add(booking)
    db.session.commit()

    newAvailableSlots = previousAvailableSlots - 1

    availableSlots = AvailableSlots(newAvailableSlots, body['locationId'])
    db.session.add(availableSlots)
    db.session.commit()

    mqttServer.clientMQTT.publish(AVAILABLE_SLOTS_TOPIC + str(body['locationId']), '{:d}'.format(newAvailableSlots), qos=QOS, retain=True)

    return jsonify({'successful': True, 'code': code}), '200 OK'

#Se l'utente ha prenotato, inserisco il parcheggio
@app.route('/enter', methods=['POST'])
def enter():
    body = request.get_json()
    now = dateutil.parser.parse(datetime.utcnow().isoformat())
    booking_minutes_ago = now - timedelta(minutes=BOOKING_MINUTES)

    if not 'type' in body or not 'locationId' in body:
        return jsonify( {'successful':False, 'error':'Some mandatory fields are missing'}), '400 Bad Request'

    if body['type'] != 'car' and body['type'] != 'device':
        return jsonify( {'successful':False, 'error':'Type must be car or device'}), '400 Bad Request'
    if body['type'] == 'device':
        if not 'code' in body:
            return jsonify({'successful': False, 'error': 'Some mandatory fields are missing'}), '400 Bad Request'

        booking = db.session.query(Booking).filter(Booking.code == body['code'], Booking.locationId == body['locationId'], Booking.bookingStatus == 'valid', Booking.timestamp >= booking_minutes_ago).order_by(Booking.timestamp.desc()).first()
    else:
        if not 'userId' in body:
            return jsonify({'successful': False, 'error': 'Some mandatory fields are missing'}), '400 Bad Request'

        booking = db.session.query(Booking).filter(Booking.userId == body['userId'], Booking.locationId == body['locationId'], Booking.bookingStatus == 'valid', Booking.timestamp >= booking_minutes_ago).order_by(Booking.timestamp.desc()).first()

    if booking == None:
        return jsonify({'successful': False, 'error': 'No valid parking reservation found'}), '401 Unauthorized'

    booking.bookingStatus = 'using'
    db.session.commit()

    parked = Parked(booking.userId, booking.locationId, currentPrice[body['locationId']], booking.code)
    db.session.add(parked)
    db.session.commit()

    return jsonify({'successful': True}), '200 OK'

@app.route('/exit', methods=['POST'])
def exit():
    body = request.get_json()

    if not 'type' in body or not 'locationId' in body:
        return jsonify( {'successful':False, 'error':'Some mandatory fields are missing'}), '400 Bad Request'

    if body['type'] != 'car' and body['type'] != 'device':
        return jsonify({'successful': False, 'error': 'Type must be car or device'}), '400 Bad Request'
    if body['type'] == 'device':
        if not 'code' in body:
            return jsonify({'successful': False, 'error': 'Some mandatory fields are missing'}), '400 Bad Request'

        booking = db.session.query(Booking).filter(Booking.code == body['code'], Booking.locationId == body['locationId'], Booking.bookingStatus == 'using').order_by(Booking.timestamp.desc()).first()
        parked = db.session.query(Parked).filter(Parked.code == body['code'], Parked.locationId == body['locationId']).order_by(Booking.timestamp.desc()).first()
    else:
        parked = db.session.query(Parked).filter(Parked.userId == body['userId'],Parked.locationId == body['locationId']).order_by(Booking.timestamp.desc()).first()
        booking = db.session.query(Booking).filter(Booking.userId == body['userId'], Booking.locationId == body['locationId'], Booking.bookingStatus == 'using',).order_by(Booking.timestamp.desc()).first()

    booking.bookingStatus = 'used'
    db.session.commit()

    if parked == None:
        return jsonify({'successful': False, 'error': 'Parking ticket not found'}), '401 Unauthorized'

    parked.exitTimestamp = datetime.utcnow()
    db.session.commit()

    #Calcolo il prezzo da pagare
    total_hour = (dateutil.parser.parse(parked.exitTimestamp.isoformat()) - dateutil.parser.parse(parked.entranceTimestamp.isoformat())).total_seconds()/3600
    totalPrice = parked.pricePerHour*total_hour

    previousAvailableSlots = db.session.query(AvailableSlots).filter(AvailableSlots.locationId == body['locationId']).order_by(AvailableSlots.timestamp.desc()).with_entities(AvailableSlots.numAvailableSlots).first()
    newAvailableSlots = previousAvailableSlots[0] + 1

    availableSlots = AvailableSlots(newAvailableSlots, body['locationId'])
    db.session.add(availableSlots)
    db.session.commit()

    mqttServer.clientMQTT.publish(AVAILABLE_SLOTS_TOPIC + body['locationId'], '{:d}'.format(newAvailableSlots), qos=QOS, retain=True)

    return jsonify({'successful': True, 'price': totalPrice}), '200 OK'

@app.route('/checkcode', methods=['POST'])
def checkCode():
    body = request.get_json()
    booking = db.session.query(Booking).filter(Booking.code == body['code'], Booking.locationId == body['locationId'], Booking.bookingStatus == 'using').order_by(Booking.timestamp.desc()).first()

    if booking != None:
        return exit()

    print ("ok")
    return enter()

@app.route('/add/<user>', methods=['POST'])
def addSlotAvailability(user):
    user = User(user)

    db.session.add(user)
    db.session.commit()
    return "ok"


@app.route('/parked', methods=['POST'])
def parked():
    content = request.get_json()
    parked = Parked(content['userId'], content['locationId'], content['pricePerHour'])

    db.session.add(parked)
    db.session.commit()
    return str('Parked OK')

@app.route('/parking', methods=['POST'])
def parking():
    content = request.get_json()
    parking = Parking(content['locationId'], content['locationName'], content['numSlots'])

    db.session.add(parking)
    db.session.commit()
    return str('Parking OK')

@app.route('/slot', methods=['POST'])
def slot():
    content = request.get_json()
    slot = Slot(content['slotId'], content['slotSection'], content['isAvailable'])

    db.session.add(slot)
    db.session.commit()
    return str('slot OK')

@app.route('/slot_availability', methods=['POST'])
def slot_availability():
    content = request.get_json()
    slot_availability = SlotAvailability(content['locationId'], content['slotId'], content['slotSection'])

    db.session.add(slot_availability)
    db.session.commit()
    return str('slot_availability OK')

@app.route('/user', methods=['POST'])
def user():
    content = request.get_json()
    user = User(content['UserId'], content['type'], content['licensePlate'])

    db.session.add(user)
    db.session.commit()
    return str('user OK')


def checkBooking():
    threading.Timer(10.0, checkBooking).start()
    validBookings = db.session.query(Booking).filter(Booking.bookingStatus == 'valid').all()
    for booking in validBookings:
        now = dateutil.parser.parse(datetime.utcnow().isoformat())
        booking_minutes_ago = now - timedelta(minutes=BOOKING_MINUTES)
        if booking.timestamp < booking_minutes_ago:
            booking.bookingStatus = "expired"
            db.session.commit()

            previousAvailableSlots = db.session.query(AvailableSlots).filter(AvailableSlots.locationId == booking.locationId).order_by(AvailableSlots.timestamp.desc()).with_entities(AvailableSlots.numAvailableSlots).first()
            if previousAvailableSlots == None:
                previousAvailableSlots = db.session.query(Parking).filter(Parking.locationId == booking.locationId).with_entities(Parking.numSlots).first()

            newAvailableSlots = previousAvailableSlots[0] + 1

            availableSlots = AvailableSlots(newAvailableSlots, booking.locationId)
            db.session.add(availableSlots)
            db.session.commit()

            mqttServer.clientMQTT.publish(AVAILABLE_SLOTS_TOPIC + str(booking.locationId), '{:d}'.format(newAvailableSlots), qos=QOS, retain=True)


if __name__ == '__main__':

    if True:  # first time (?)
        db.create_all()

    port = 80
    interface = '0.0.0.0'

    checkBooking()

    global mqttServer
    mqttServer = MQTTServer()
    mqttServer.setup()

    app.run(host=interface, port=port)