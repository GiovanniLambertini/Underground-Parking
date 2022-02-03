#sample1
# first example

# see https://flask.palletsprojects.com/en/1.1.x/

from flask import Flask


appname = "IOT - sample1"
app = Flask(appname)

@app.route('/')
def testoHTML():
    return '<h1>I love IoT</h1>'

if __name__ == '__main__':
    app.run()