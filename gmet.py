#Import list
import re
import json
import time
import datetime
import argparse
from urllib.request import urlopen

#Color definitions
CFLASH =  '\033[7;1m' # White Background, Bold black Text
CGREEN =  '\033[32;1m' # Green Bold Text
CORANGE =  '\033[33;1m' # Orange Bold Text
CBLUE =  '\033[34;1m' # Blue Bold Text
CEND = '\033[0m' # reset to the defaults

#parse options
#-c cityname / default is geolocalized
#-d offset for the prevision day / default is today i.e. d=0
#-s summary view i.e. display all data received in a summarised manner
#-m select meteo server source / default is meteofrance. Other sources are ...
#-h print this help
def parse() :
    parser = argparse.ArgumentParser(description='Command Line utility to access Meteo data from various sources')
    parser.add_argument('offset', nargs='*', type=int, help='offset in days compared to today, i.e. 0 means today, 1 means tomorrow,...')
    parser.add_argument('--city', '-c', dest='city', help='cityname, if no value is provided, automatically guessed via the geolocalized IP adress')
    parser.add_argument('--summary', '-s', dest='summary', action='count', help='summary view, i.e. gives all data received from server in a synthetic way')
    parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.9')
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

#Build the right output screen with details at day level, period level, and range of our level, refining data when available
def formatOutput(iConfig, iData):
    #Define range of date to display base on command line inputs
    if not iConfig.offset:
        iConfig.offset.append(0)
        if datetime.datetime.now().hour>16:
            iConfig.offset.append(1)
    myRange = range(min(iConfig.offset), max(iConfig.offset)+1)
    
    displayCondensed = False
    if iConfig.summary:
        #Display the 10 days of daily prevision in resumes section
        myRange = range(0, 100)
        if iConfig.summary > 1:
            displayCondensed = True

    #Do the actual display
    for i in myRange:
        keyResumes = str(i)+'_resume'
        if keyResumes in iData['result']['resumes']:
            timeString = time.strftime("%d%b-%a", time.gmtime(iData['result']['resumes'][keyResumes]['date'] / 1000))
            #TODO: Change the color Orange/Blue/Green based on the prevision (sun or rain) available in variable iData['result']['resumes'][keyResumes]['description']
            #BLUE if contains pluie or averse
            #ORANGE if contains soleil or ??
            #GREEN otherwise
            COLOR = CGREEN
            if re.search('pluie', iData['result']['resumes'][keyResumes]['description'].lower()):
                COLOR = CBLUE
            if re.search('averse', iData['result']['resumes'][keyResumes]['description'].lower()):
                COLOR = CBLUE
            if re.search('soleil', iData['result']['resumes'][keyResumes]['description'].lower()):
                COLOR = CORANGE
            print(COLOR + "{} | {:<17} | T: {:>2}-{:>2}".format(timeString, iData['result']['resumes'][keyResumes]['description'], iData['result']['resumes'][keyResumes]['temperatureMin'], iData['result']['resumes'][keyResumes]['temperatureMax']) + CEND)

        # This boolean test if the display should be a super condensed one keeping only values at day level
        if not displayCondensed:
            #Then, display the prevision "by range matin, midi, soir, nuit" in previsions section
            for r in ['matin', 'midi', 'soir', 'nuit']:
                keyPrevisions = str(i)+'_'+r
                if keyPrevisions in iData['result']['previsions']:
                    detailDisplayed = False
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
                            print('  * {:>5} | {:<17} | T: {:>2}-{:>2} | V: {:<3} Pluie?: {:>2}%'.format(keyPrevisions48h[2:], iData['result']['previsions48h'][keyPrevisions48h]['description'], iData['result']['previsions48h'][keyPrevisions48h]['temperatureMin'], iData['result']['previsions48h'][keyPrevisions48h]['temperatureMax'], iData['result']['previsions48h'][keyPrevisions48h]['vitesseVent'], iData['result']['previsions48h'][keyPrevisions48h]['probaPluie']))
                            detailDisplayed = True

                    if not detailDisplayed:
                        print(' -> {:>5} | {:<17} | T: {:^6}| V: {:<3}'.format(r, iData['result']['previsions'][keyPrevisions]['description'], iData['result']['previsions'][keyPrevisions]['temperatureCarte'], iData['result']['previsions'][keyPrevisions]['vitesseVent']))

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

    print(CFLASH + '-- Meteo forecast -- {} ({}) --'.format(data['city'],data['country']) + '                        ' + CEND)    
    data = getDataFromMeteoFranceAPI(data['insee'])
    formatOutput(args, data)

