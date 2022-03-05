# sample11
# objects
#pip install flask-sqlalchemy
#pip install pymysql

from flask import Flask
from config import Config
from flask import render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

appname = "IOT - sample1"
app = Flask(appname)
myconfig = Config
app.config.from_object(myconfig)

# db creation
db = SQLAlchemy(app)

class Sensorfeed(db.Model):
    id = db.Column('student_id', db.Integer, primary_key = True)
    value = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False,  default=datetime.utcnow)

    def __init__(self, value):
        self.value = value

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
    availablePlaces = db.Column(db.Integer)
    isAvailable = db.Column(db.Boolean)

    def __init__(self, locationId, slotId, slotSection, availablePlaces, isAvailable):
        self.locationId = locationId
        self.slotId = slotId
        self.slotSection = slotSection
        self.availablePlaces = availablePlaces
        self.isAvailable = isAvailable

class Booking(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), primary_key=True)
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    def __init__(self, userId, locationId):
        self.userId = userId
        self.locationId = locationId



class Parked(db.Model):
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'), primary_key=True)
    locationId = db.Column(db.Integer, db.ForeignKey('parking.locationId'), primary_key=True)
    entranceTimestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.utcnow)      #Booking/Entrance timestamp
    duration = db.Column(db.Integer)                                                                        #Duration in seconds
    pricePerHour = db.Column(db.Float)

    def __init__(self, userId, locationId, duration, pricePerHour):
        self.userId = userId
        self.locationId = locationId
        self.duration = duration
        self.pricePerHour = pricePerHour



@app.errorhandler(404)
def page_not_found(error):
    return 'Errore', 404

@app.route('/')
def testoHTML():
    if request.accept_mimetypes['application/json']:
        return jsonify( {'text':'Alex Costa'}), '200 OK'
    else:
        return '<h1>I love IoT</h1>'

@app.route('/prova', methods=['GET'])
def prova():
    elenco=User.query.order_by(User.userId.desc()).limit(10).all()

    string = ''
    for el in elenco:
        string += str(el.userId) + ', '

    return string

@app.route('/booking', methods=['POST'])
def bookParkSlot():
    content = request.get_json()
    booking = Booking(content['userId'], content['location'])

    db.session.add(booking)
    db.session.commit()
    return str('Booking OK')


@app.route('/addinlista/<val>', methods=['POST'])
def addinlista(val):
    sf = Sensorfeed(val)

    db.session.add(sf)
    db.session.commit()
    return str(sf.id)

@app.route('/add/<user>', methods=['POST'])
def addSlotAvailability(user):
    user = User(user)

    db.session.add(user)
    db.session.commit()
    return "ok"


if __name__ == '__main__':

    if True:  # first time (?)
        db.create_all()

    port = 80
    interface = '0.0.0.0'
    app.run(host=interface, port=port)