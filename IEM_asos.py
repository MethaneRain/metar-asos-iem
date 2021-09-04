"""
Example script that scrapes data from the IEM ASOS download service

The only argument is for station(s).
------------------------------------
Example:
    $ python IEM_asos.py CO -> get all Colorado stations
"""
from __future__ import print_function
import json
import time, sys
import datetime
# Python 2 and 3: alternative 4
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

# Number of attempts to download data
MAX_ATTEMPTS = 6
# HTTPS here can be problematic for installs that don't have Lets Encrypt CA
SERVICE = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"


def download_data(uri):
    """Fetch the data from the IEM
    The IEM download service has some protections in place to keep the number
    of inbound requests in check.  This function implements an exponential
    backoff to keep individual downloads from erroring.
    Args:
      uri (string): URL to fetch
    Returns:
      string data
    """
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            data = urlopen(uri, timeout=300).read().decode('utf-8')
            if data is not None and not data.startswith('ERROR'):
                return data
        except Exception as exp:
            print("download_data(%s) failed with %s" % (uri, exp))
            time.sleep(5)
        attempt += 1

    print("Exhausted attempts to download, returning empty data")
    return ""


def get_stations_from_filelist(filename):
    """Build a listing of stations from a simple file listing the stations.
    The file should simply have one station per line.
    """
    stations = []
    for line in open(filename):
        stations.append(line.strip())
    return stations


def get_stations_from_networks():
    """Build a station list by using a bunch of IEM networks."""
    stations = []
    #states = """AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
    # MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
    # WA WI WV WY"""
    states = f"""{sys.argv[1]}"""
    # IEM quirk to have Iowa AWOS sites in its own labeled network
    networks = ['AWOS']
    for state in states.split():
        networks.append("%s_ASOS" % (state,))

    for network in networks:
        # Get metadata
        uri = ("https://mesonet.agron.iastate.edu/"
               "geojson/network/%s.geojson") % (network,)
        data = urlopen(uri)
        jdict = json.load(data)
        for site in jdict['features']:
            stations.append(site['properties']['sid'])
    return stations




def main():
    """Our main method"""
    # timestamps in UTC to request data for
    #startts = datetime.datetime(2021, 7, 11,12)
    #endts = datetime.datetime(2021, 7, 12,18)


    startts = input("start date? ** year (2021), month number (7), day (11), and hour (12)")
    endts = input("end date? ** leave blank for same as start date")
    time_vals = startts.split()
    time_vals = map(int, time_vals)
    time_vals = list(time_vals)

    startts2 = datetime.datetime(*time_vals)
    if endts == "":
        endts2 = startts2
    else:
        end_time_vals = endts.split()
        end_time_vals = list(map(int, end_time_vals))
        endts2 = datetime.datetime(*end_time_vals)

    service = SERVICE + "data=all&tz=Etc/UTC&format=comma&latlon=yes&"

    service += startts2.strftime('year1=%Y&month1=%m&day1=%d&')
    service += endts2.strftime('year2=%Y&month2=%m&day2=%d&')

    # Two examples of how to specify a list of stations
    stations = get_stations_from_networks()
    # stations = get_stations_from_filelist("mystations.txt")
    for station in stations:
        uri = '%s&station=%s' % (service, station)
        print('Downloading: %s' % (station, ))
        data = download_data(uri)
        outfn = '%s_%s_%s.txt' % (station, startts2.strftime("%Y%m%d%H%M"),
                                  endts2.strftime("%Y%m%d%H%M"))

        path = "data/"
        out = open(path+outfn, 'w')
        out.write(data)
        out.close()
    print("\nAll done.")
        
if __name__ == '__main__':
    main()
