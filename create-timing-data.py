import csv
from optparse import OptionParser

from api.get_match_times import FMSAPIGetTimes


def tba_key_from_match(eventKey, matchDict):
    """
    Creates a TBA formed match key from the API response
    2015 game specific
    """

    # Will be {Qualification, Quarterfinal, Semifinal, Finals} N
    desc = matchDict['description'].split()
    if desc[0] == "Qualification":
        matchKey = "qm{}".format(desc[1])
    elif desc[0] == "Quarterfinal":
        matchKey = "qf1m{}".format(desc[1])
    elif desc[0] == "Semifinal":
        matchKey = "sf1m{}".format(desc[1])
    elif desc[0] == "Finals":
        matchKey = "f1m{}".format(desc[1])
    else:
        print "Couldn't get TBA key from Description {}".format(matchDict['description'])
    return "{}_{}".format(eventKey, matchKey)


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
