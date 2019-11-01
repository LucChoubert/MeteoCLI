#Import list
import json
import time
import argparse
from urllib.request import urlopen

#parse options
#-c cityname / default is geolocalized
#-d offset for the prevision day / default is today i.e. d=0
#-s summary view i.e. display all data received in a summarised manner
#-m select meteo server source / default is meteofrance. Other sources are ...
#-h print this help
def parse() :
    parser = argparse.ArgumentParser(description='Command Line utility to access Meteo data from various sources')
    parser.add_argument('--city', '-c', dest='city', help='cityname, if no value is provided, automatically guessed via the geolocalized IP adress')
    return parser.parse_args()


#function to localize the computer
def localize() :
    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    data = json.load(response)

    IP=data['ip']
    city = data['city']
    postal = data['postal']
    region = data['region']
    country = data['country']
    org = data['org']

    d = dict();
    d['ip'] = data['ip']
    d['city'] = data['city']
    d['zip']   = data['postal']
    d['country'] = data['country']

    return d

#function to get INSEE code of the city
#TODO: error management vie exception
def getInseeCode(iCityName):
    url = 'http://ws.meteofrance.com/ws/getLieux/' + iCityName + '.json'
    response = urlopen(url)
    data = json.load(response)
    if ( len(data['result']['france']) == 1):
        return data['result']['france'][0]['indicatif'], data['result']['france'][0]['codePostal'], data['result']['france'][0]['pays']
    else:
        print('Error - too many or too few Insee code for this city name')

#function to get meteo data from MeteoFrance
def getDataFromMeteoFranceAPI( iCityInseeCode ):
    #Biot url: http://ws.meteofrance.com/ws/getDetail/france/060180.json
    url = 'http://ws.meteofrance.com/ws/getDetail/france/' + iCityInseeCode + '.json'
    response = urlopen(url)
    data = json.load(response)
    #timeString = time.strftime("%d %b %Y, %a", time.gmtime(data['result']['resumes']['0_resume']['date'] / 1000))
    #print(timeString + " T-Min:{1} T-Max:{2} Météo: {0}".format(data['result']['resumes']['0_resume']['description'],data['result']['resumes']['0_resume']['temperatureMin'],data['result']['resumes']['0_resume']['temperatureMax']))
    for i in range(0, 9):
        keyString = str(i)+'_resume'
        timeString = time.strftime("%d %b %Y, %a", time.gmtime(data['result']['resumes'][keyString]['date'] / 1000))
        print(timeString + " T-Min:{1} T-Max:{2} Météo: {0}".format(data['result']['resumes'][keyString]['description'],data['result']['resumes'][keyString]['temperatureMin'],data['result']['resumes'][keyString]['temperatureMax']))    

#Main function
if __name__ == '__main__':
    args = parse()
    data = {}
    if args.city is None:
        data = localize()
    else:
        data['ip'] = None
        data['city'] = args.city
    data['insee'], data['zip'], data['country'] = getInseeCode(data['city'])

    print('Meteo forecast -- City: {1}  Zip: {2}  Insee: {3}  Country: {4}'.format(data['ip'],data['city'],data['zip'],data['insee'],data['country']))    
    getDataFromMeteoFranceAPI(data['insee'])
