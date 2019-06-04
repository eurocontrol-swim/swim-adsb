"""
Copyright 2019 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the 
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following 
   disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following 
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products 
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE 
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open Source Initiative: 
http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""
from swim_adsb.adsb.traffic import OpenSkyNetworkDataHandler

__author__ = "EUROCONTROL (SWIM)"

airports = {
    'Brussels': 'EBBR',
    'Amsterdam': 'EHAM',
    'Paris': 'LFPG',
    'Berlin': 'EDDB',
    'Athens': 'LGAV'
}


opensky = OpenSkyNetworkDataHandler()


def test_traffic():

    states = opensky._get_states()
    states_dict = {state.icao24: state for state in states if state.icao24}

    for city, code in airports.items():
        arrivals = opensky._arrivals_today_handler(code)
        arrivals_dict = {arr.icao24: arr for arr in arrivals if arr.icao24}


        print(f"Arrivals in {city}")
        for arr_icao24, arr in arrivals_dict.items():
            state = states_dict.get(arr_icao24)

            if state is None:
                continue

            print(f"{state.icao24} flying from {arr.est_departure_airport}: {state.latitude}, {state.longitude}")


        departures = opensky._departures_today_handler(code)
        departures_dict = {arr.icao24: arr for arr in departures if arr.icao24}

        print(f"Departures from {city}")
        for dep_icao24, dep in departures_dict.items():
            state = states_dict.get(dep_icao24)

            if state is None:
                continue

            print(f"{state.icao24} flying to {dep.est_arrival_airport}: {state.latitude}, {state.longitude}")
