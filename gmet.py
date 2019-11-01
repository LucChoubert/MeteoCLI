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
    parser.add_argument('--offset', '-o', dest='offset', type=int, default=0, help='offset in days compared to today, i.e. 0 means today, 1 means tomorrow,...')
    parser.add_argument('--summary', '-s', dest='summary', action='store_true', help='summary view, i.e. gives all data received from server in a synthetic way')
    return parser.parse_args()


#function to localize the computer
def localize() :
    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    data = json.load(response)

    d = dict()
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
    return data

def formatOutput(iConfig, iData):
    #timeString = time.strftime("%d %b %Y, %a", time.gmtime(iData['result']['resumes']['0_resume']['date'] / 1000))
    #print(timeString + " T-Min:{1} T-Max:{2} Météo: {0}".format(iData['result']['resumes']['0_resume']['description'],iData['result']['resumes']['0_resume']['temperatureMin'],iData['result']['resumes']['0_resume']['temperatureMax']))
    myRange = range(iConfig.offset, iConfig.offset+1)
    if iConfig.summary:
        #Display the 10 days of daily prevision in resumes section
        myRange = range(0, 100)
    for i in myRange:
        keyResumes = str(i)+'_resume'
        if keyResumes in iData['result']['resumes']:
            timeString = time.strftime("%d%b-%a", time.gmtime(iData['result']['resumes'][keyResumes]['date'] / 1000))
            print("\n{} | {:<17} | T: {:>2}-{:>2}".format(timeString, iData['result']['resumes'][keyResumes]['description'], iData['result']['resumes'][keyResumes]['temperatureMin'], iData['result']['resumes'][keyResumes]['temperatureMax']))

        #Then, display the prevision "by range matin, midi, soir, nuit" in previsions section
        for r in ['matin', 'midi', 'soir', 'nuit']:
            keyPrevisions = str(i)+'_'+r
            if keyPrevisions in iData['result']['previsions']:
                print(' -> {:>5} | {:<17} | T: {:^6}| V: {:<3}'.format(r, iData['result']['previsions'][keyPrevisions]['description'], iData['result']['previsions'][keyPrevisions]['temperatureCarte'], iData['result']['previsions'][keyPrevisions]['vitesseVent']))
                l = []
                if r == 'matin':
                    l = [str(i) + '_' + x for x in ['07-10', '10-13']]
                if r == 'midi':
                    l = [str(i) + '_' + x for x in ['13-16', '16-19']]
                if r == 'soir':
                    l = [str(i) + '_' + x for x in ['19-22']]
                if r == 'nuit':
                    l = [str(i) + '_' + x for x in ['22-01']] + [str(i+1) + '_' + x for x in ['01-04', '04-07']]                
                
                for keyPrevisions48h in l:
                    if keyPrevisions48h in iData['result']['previsions48h']:
                        print('  *{:>5} | {:<17} | T: {:>2}-{:>2} | V: {:<3} Pluie?: {:>2}%'.format(keyPrevisions48h[1:], iData['result']['previsions48h'][keyPrevisions48h]['description'], iData['result']['previsions48h'][keyPrevisions48h]['temperatureMin'], iData['result']['previsions48h'][keyPrevisions48h]['temperatureMax'], iData['result']['previsions48h'][keyPrevisions48h]['vitesseVent'], iData['result']['previsions48h'][keyPrevisions48h]['probaPluie']))

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

    print('Meteo forecast -- City: {0}  Zip: {1}  Insee: {2}  Country: {3}'.format(data['city'],data['zip'],data['insee'],data['country']))    
    data = getDataFromMeteoFranceAPI(data['insee'])
    formatOutput(args, data)
