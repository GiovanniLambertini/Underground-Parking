#pip install flask-sqlalchemy
#pip install pymysql

from flask import Flask
from config import Config
from flask import render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
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
BOOKING_MINUTES = 35
currentPrice = 0

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
    availableSlots = db.Column(db.Integer)
    bookingStatus = db.Column(db.String(10), default="valid")

    def __init__(self, userId, locationId):
        self.userId = userId
        self.locationId = locationId

    def __init__(self, userId, locationId, code, availableSlots):
        self.userId = userId
        self.locationId = locationId
        self.code = code
        self.availableSlots = availableSlots

class Parked(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), primary_key=True)
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    entranceTimestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)      #Entrance timestamp
    exitTimestamp = db.Column(db.DateTime(timezone=True), nullable=True)                                    #Exit timestamp
    pricePerHour = db.Column(db.Float)

    def __init__(self, userId, locationId, pricePerHour):
        self.userId = userId
        self.locationId = locationId
        self.pricePerHour = pricePerHour

class MQTTSubscriber():

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting mqtt...")
        self.clientMQTT.connect("broker.emqx.io", 1883, 60)

        self.clientMQTT.loop_start()



    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        self.clientMQTT.subscribe(REQUEST_CODE_TOPIC)


    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if REQUEST_CODE_TOPIC in msg.topic:
            #self.ser.write (msg.payload)
            accessCode = random.randint(0, 99999)
            self.clientMQTT.publish(CLIENT_ID, '{:d}'.format(accessCode))
            self.bookedCodes.append(accessCode)

        elif PRICE_TOPIC in msg.topc:
            ...


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

    if body['type'] != 'car' and body['type'] != 'device':
        return jsonify( {'successful':False, 'error':'Type must be car or device'}), '400 Bad Request'
    if body['type'] == 'car':
        booking = Booking(body['userId'], body['locationId'])
        db.session.add(booking)
        db.session.commit()

        return jsonify( {'successful':True}), '200 OK'

    else:
        repeat=True
        while (repeat):
            #Generate 5 digits code
            code = "*"
            for i in range(CODE_LENGTH):
                code += str(random.randint(0,9))
            code += "#"

            #Controllo che il codice non sia già stato assegnato
            now = datetime.fromisoformat(datetime.utcnow().isoformat())
            booking_minutes_ago = now - timedelta(minutes=BOOKING_MINUTES*2)
            usedCodes = db.session.query(Booking).filter(Booking.locationId == body['locationId'], Booking.timestamp >= booking_minutes_ago).with_entities(Booking.code).all()

            if (code, ) not in usedCodes:
                repeat = False

        availableSlots = db.session.query(Booking).filter(Booking.locationId == body['locationId']).order_by(Booking.timestamp.desc()).with_entities(Booking.availableSlots).first()
        if availableSlots == None:
            availableSlots = db.session.query(Parking).filter(Parking.locationId == body['locationId']).with_entities(Parking.numSlots).first()

        booking = Booking(body['userId'], body['locationId'], code, availableSlots[0]-1)
        db.session.add(booking)
        db.session.commit()

        return jsonify({'successful': True, 'code': code}), '200 OK'

#Controllo se l'utente ha prenotato, inserisco il parcheggio
@app.route('/enter', methods=['POST'])
def enter():
    body = request.get_json()
    now = datetime.fromisoformat(datetime.utcnow().isoformat())
    booking_minutes_ago = now - timedelta(minutes=BOOKING_MINUTES)

    if body['type'] != 'car' and body['type'] != 'device':
        return jsonify( {'successful':False, 'error':'Type must be car or device'}), '400 Bad Request'
    if body['type'] == 'device':
        booking = db.session.query(Booking).filter(Booking.code == body['code'], Booking.locationId == body['locationId'], Booking.timestamp >= booking_minutes_ago).order_by(Booking.timestamp.desc()).first()
    else:
        booking = db.session.query(Booking).filter(Booking.userId == body['userId'], Booking.locationId == body['locationId'], Booking.timestamp >= booking_minutes_ago).order_by(Booking.timestamp.desc()).first()

    if booking == None:
        return jsonify({'successful': False, 'error': 'Parking reservation not found'}), '401 Unauthorized'

    booking = Parked(booking.userId, booking.locationId, currentPrice)
    db.session.add(booking)
    db.session.commit()

    return jsonify({'successful': True}), '200 OK'

@app.route('/exit', methods=['POST'])
def exit():
    body = request.get_json()

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
    threading.Timer(1.0, checkBooking).start()
    validBookings = db.session.query(Booking).filter(Booking.bookingStatus == 'valid').all()
    for booking in validBookings:
        now = datetime.fromisoformat(datetime.utcnow().isoformat())
        booking_minutes_ago = now - timedelta(minutes=BOOKING_MINUTES)
        if booking.timestamp < booking_minutes_ago:
            booking.bookingStatus = "expired"
            db.session.commit()

if __name__ == '__main__':

    if True:  # first time (?)
        db.create_all()

    port = 80
    interface = '0.0.0.0'

    checkBooking()

    app.run(host=interface, port=port)