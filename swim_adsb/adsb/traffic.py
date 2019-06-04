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
from datetime import datetime, timedelta
from functools import lru_cache

from cachetools import cached, TTLCache
from opensky_network_client.opensky_network import OpenskyNetworkClient

__author__ = "EUROCONTROL (SWIM)"


def _today():
    today = datetime.today()
    begin = datetime(today.year, today.month, today.day, 0, 0) - timedelta(days=1)
    end = datetime(today.year, today.month, today.day, 23, 59, 59)

    return int(begin.timestamp()), int(end.timestamp())


class OpenSkyNetworkDataHandler:
    def __init__(self):
        self.client = OpenskyNetworkClient.create('opensky-network.org', timeout=30)

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def _arrivals_today_handler(self, icao):
        begin, end = _today()

        try:
            result = self.client.get_flight_arrivals(icao, begin, end)
        except Exception as e:
            print(str(e))
            result = []

        return result

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def _departures_today_handler(self, icao):
        begin, end = _today()

        try:
            result = self.client.get_flight_departures(icao, begin, end)
        except Exception as e:
            print(str(e))
            result = []

        return result

    def _get_states(self):
        try:
            states = self.client.get_states()
            result = states.states
        except Exception as e:
            print(str(e))
            result = []

        return result

    def get_states_dict(self):
        states = self._get_states()

        return {state.icao24: state for state in states}

    def arrivals_handler(self, airport, pre_data=None):
        return self._flight_connection_handler(airport,
                                               states_dict=pre_data,
                                               get_flight_connections_handler=self._arrivals_today_handler)


    def departures_handler(self, airport, pre_data=None):
        return self._flight_connection_handler(airport,
                                               states_dict=pre_data,
                                               get_flight_connections_handler=self._departures_today_handler)

    def _flight_connection_handler(self, airport, states_dict, get_flight_connections_handler):
        flight_connections = get_flight_connections_handler(airport)

        flight_connections_dict = {fc.icao24: fc for fc in flight_connections if fc.icao24}

        flight_connections_with_state = {icao24: fc for icao24, fc in flight_connections_dict.items()
                                         if icao24 in states_dict}

        data = [self._get_flight_data(states_dict.get(fc_icao24), fc)
                for fc_icao24, fc in flight_connections_with_state.items()]

        return data


    def _get_flight_data(self, state, flight_connection):
        # from_airport = self._get_airport_name(icao=flight_connection.est_departure_airport)
        # to_airport = self._get_airport_name(icao=flight_connection.est_arrival_airport)
        from_airport = flight_connection.est_departure_airport or "Unknown airport"
        to_airport = flight_connection.est_arrival_airport or "Unknown airport"

        return {
            'icao24': state.icao24,
            'lat': state.latitude,
            'lng': state.longitude,
            'from': from_airport,
            'to': to_airport,
            'last_contact': state.last_contact_in_sec
        }

    @lru_cache(maxsize=None)
    def _get_airport_name(self, icao):
        try:
            airport = self.client.get_airport(icao=icao)
        except Exception as e:
            print(f"Couldn't find airport {icao}: {str(e)}")
            return "Unknown airport"

        return f"{airport.name}, {airport.municipality}"
