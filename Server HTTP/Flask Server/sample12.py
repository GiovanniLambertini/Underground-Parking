# sample11
# objects
#pip install flask-sqlalchemy


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



@app.errorhandler(404)
def page_not_found(error):
    return 'Errore', 404

@app.route('/')
def testoHTML():
    if request.accept_mimetypes['application/json']:
        return jsonify( {'text':'I Love IoT'}), '200 OK'
    else:
        return '<h1>I love IoT</h1>'


@app.route('/lista', methods=['GET'])
def stampalsita():
    elenco=Sensorfeed.query.all()

    return render_template('lista3.html', lista=elenco)

@app.route('/addinlista/<val>', methods=['POST'])
def addinlista(val):
    sf = Sensorfeed(val)

    db.session.add(sf)
    db.session.commit()
    return str(sf.id)



if __name__ == '__main__':

    if True:  # first time (?)
        db.create_all()

    port = 80
    interface = '0.0.0.0'
    app.run(host=interface,port=port)