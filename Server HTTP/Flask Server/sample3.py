# sample3
# add more routes, with parameters

from flask import Flask


appname = "IOT - sample1"
app = Flask(appname)


@app.route('/')
def testoHTML():
    return '<h1>I love IoT</h1>'


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)

@app.route('/ciao')
def hello_name2():
    return "Hello ciao specific!"


if __name__ == '__main__':
    port = 10000
    interface = '0.0.0.0'
    app.run(host=interface,port=port)