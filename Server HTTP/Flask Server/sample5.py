#sample5
# configuration

from flask import Flask
from config import Config


appname = "IOT - sample1"
app = Flask(appname)
myconfig = Config()
app.config.from_object(myconfig)

elenco=[]

@app.route('/')
def testoHTML():
    return '<h1>I love IoT</h1>'


@app.route('/lista')
def stampalsita():
    txt = ";".join(elenco)
    return txt

@app.route('/addinlista/<name>')
def addinlista(name):
    elenco.append(name)
    return str(len(elenco))


@app.route('/lista')
def hello_name(name):
    return "Hello {}!".format(name)

if __name__ == '__main__':

    app.run(host=app.config.get('FLASK_RUN_HOST','0.0.0.0'), port=app.config.get('FLASK_RUN_PORT',80))