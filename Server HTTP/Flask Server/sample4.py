# sample4
# vector

from flask import Flask


appname = "IOT - sample1"
app = Flask(appname)

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
    port = 10000
    interface = '0.0.0.0'
    app.run(host=interface,port=port)