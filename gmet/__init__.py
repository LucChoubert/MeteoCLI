from flask import Flask
from gmet import gmet

if __name__ == '__main__':
    #Main function
    gmet.run()


app = Flask(__name__)

@app.route('/<iCity>')
def meteo(iCity):
    return gmet.runWeb(iCity)