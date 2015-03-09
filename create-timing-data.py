import csv
from optparse import OptionParser

from api.get_match_times import FMSAPIGetTimes


def tba_key_from_match(eventKey, matchDict):
    """
    Creates a TBA formed match key from the API response
    2015 game specific
    """

    level = matchDict['level']
    matchNum = int(matchDict['matchNumber'])

    if level == 'Qualification':
        matchKey = 'qm{}'.format(matchNum)
    elif level == 'Playoff':
        if matchNum >= 1 and matchNum <= 8:
            matchKey = 'qf1m{}'.format(matchNum)
        elif matchNum >= 9 and matchNum <= 14:
            matchKey = 'sf1m{}'.format(matchNum - 8)
        else:
            matchKey = 'f1m{}'.format(matchNum - 14)
    else:
        print "Unable to get key from {} match {}".format(level, matchNum)
    return matchKey


def parse_api_data(eventKey, matchList):
    dataFile = "times/{}_times.csv".format(eventKey)
    with open(dataFile, "a") as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='\\', quoting=csv.QUOTE_MINIMAL)
        for match in matchList:
            writer.writerow([tba_key_from_match(eventKey, match), match['autoStartTime']])

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("--eventKey", dest="eventKey", help="TBA Event Key")

    (options, args) = parser.parse_args()

    eventKey = options.eventKey
    datafeed = FMSAPIGetTimes('api.conf')
    resp = datafeed.getTimeData(eventKey[:4], eventKey[4:])
    parse_api_data(eventKey, resp['Matches'])
