import os
from flask import Flask, request, send_from_directory
from gmet import gmet

if __name__ == '__main__':
    #Main function
    gmet.run()


app = Flask(__name__)

#Static Files
#app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

#Dynamic URLs
@app.route('/')
@app.route('/<city>')
def meteo(city=None):
    if 'X-Client-Ip' in request.headers:
        aCallingIP = request.headers['X-Client-Ip']
    else:
        aCallingIP = request.remote_addr
    return gmet.runWeb(iIP=aCallingIP, iCity=city, )

@app.route('/debug')
def debug():
    output_buffer="HTTP headers:{} \nURL: {}".format(str(request.headers), str(request))
    return output_buffer