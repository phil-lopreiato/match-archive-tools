import base64
import ConfigParser
import json
import urllib2


class FMSAPIGetTimes(object):

    BASE_URL = 'https://frc-api.usfirst.org/api/v1.0'
    MATCHES_ENDPOINT = BASE_URL + '/matches/{}/{}'  # year, eventShort

    def __init__(self, filepath):
        config = ConfigParser.ConfigParser()
        config.readfp(open(filepath))

        username = config.get('fmsapi', 'username')
        secret = config.get('fmsapi', 'secret')

        self.auth_token = base64.b64encode('{}:{}'.format(username, secret))

    def _fetch(self, url):

        request = urllib2.Request(url)
        request.add_header('Authorization', 'Basic {}'.format(self.auth_token))

        try:
            resp = urllib2.urlopen(request)
        except urllib2.HTTPError, e:
            print "request failed for: {}".format(url)
            print "code: {}, reason: {}".format(e.code, e.reason)
            return None

        return json.loads(resp.read())

    def getTimeData(self, year, eventShort):
        url = self.MATCHES_ENDPOINT.format(year, eventShort)
        print "Fetching {}".format(url)
        return self._fetch(url)
