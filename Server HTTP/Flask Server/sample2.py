# sample2
# change port and interface

from flask import Flask


appname = "IOT - sample1"
app = Flask(appname)

@app.route('/')
def testoHTML():
    return '<h1>I love IoT</h1>'

if __name__ == '__main__':
    port = 10000
    interface = '0.0.0.0'
    app.run(host=interface,port=port)