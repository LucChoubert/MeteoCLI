#Import list
import re
import json
import time
import datetime
import argparse
import logging
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
    parser.add_argument('--city', '-c', dest='city', help='the City name for which we want weather forecast, if no value is provided, automatically guessed via the geolocalized IP adress')
    parser.add_argument('--inseecode', '-ic', dest='inseecode', default=None, help='the Insee Code of the city, this option is to be used in case of ambiguity, when the city name provided, or guessed by ip localisation match with more than one city name')
    parser.add_argument('--summary', '-s', dest='summary', action='count', help='summary view, i.e. gives all data received from server in a synthetic way')
    parser.add_argument('--log', '-l', metavar='log_level', dest='loglevel', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'], default='INFO', help='set the log level DEBUG, INFO, WARNING, ERROR or CRITICAL')
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
def getInseeCode(iCityName, iInseeCode=None):
    url = 'http://ws.meteofrance.com/ws/getLieux/' + iCityName + '.json'
    response = urlopen(url)
    data = json.load(response)
    logging.debug("API answer\n" + json.dumps(data))
    if ( len(data['result']['france']) == 0):
        logging.error('Error - Input City name is unknown: '+iCityName)
        raise ValueError('Error - Input City name is unknown: '+iCityName)
    else:
        #The following code support case where one insee code is returned or when several are returned like in antibes
        #In case of ambiguity, libe with bordeaux, the additional iInseeCode may be used if provided, if not, firt one is used and the rest are logged
        k=None
        candidate_list = {}

        for e in data['result']['france']:
            #Regroup by code postal to see if there is only one at the end, works well for antibes. Also use iInseeCode to filter out those not wished
            if (e['codePostal'] not in candidate_list) or (e['nom']==iCityName):
                if iInseeCode==None or e['indicatif'] == iInseeCode:
                    candidate_list[e['codePostal']] = [e['indicatif'], e['nom'], e['codePostal'], e['nomDept'],e['numDept'], e['pays']]

        if ( len(candidate_list) == 0):
            logging.error('Error - Input Insee code is not compatible with City name: '+iCityName+' vs '+iInseeCode)
            raise ValueError('Error - Input Insee code is not compatible with City name: '+iCityName+' vs '+iInseeCode)

        if len(candidate_list) > 1:
            #More than one city is matching: log all choices and select arbitrarily the first one
            logging.warning("More than one city correspond to that name, meteo retrieved from 1st one only. Use inseecode argument to change it")
            logging.warning("InseeCode - City - Zip Code - Department Name")
            for e in candidate_list:
                logging.warning(candidate_list[e][0]+' - '+candidate_list[e][1]+' - '+candidate_list[e][2]+' - '+candidate_list[e][3])

        k = list(candidate_list)[0]
        return candidate_list[k]

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

    #log_format='%(asctime)s %(module)s.%(funcName)s:%(levelname)s:%(message)s'
    log_format='%(levelname)s:%(message)s'
    logging.basicConfig(format=log_format,
                        datefmt='%d/%m/%Y %H:%M:%S',
    #                   filename=args.log_file,
                        level=args.loglevel)

    data = {}
    if args.city is None:
        logging.debug("No city, trying to localize")
        data = localize()
        logging.debug(data)
    else:
        data['ip'] = None
        data['city'] = args.city

    try:
        data['insee'], data['city'], data['zip'], data['depName'], data['depNum'], data['country'] = getInseeCode(data['city'], args.inseecode)

        print(CFLASH + '-- Meteo forecast -- {} ({} - {}) --'.format(data['city'],data['depNum'],data['country']) + '                        ' + CEND)    
        data = getDataFromMeteoFranceAPI(data['insee'])
        formatOutput(args, data)
        exit(0)

    except ValueError as error:
        logging.debug("Exception Catched:"+str(type(error)))
        exit(1)