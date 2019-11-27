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
import json
import logging
from datetime import datetime, timedelta
from typing import Tuple, List, Callable, Dict, Optional, Union, Any

from cachetools import cached, TTLCache
from opensky_network_client.models import FlightConnection, StateVector
from opensky_network_client.opensky_network import OpenskyNetworkClient
from proton import Message

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)

AirTrafficDataType = Dict[str, Union[str, float, int]]


class AirTraffic:
    def __init__(self, traffic_timespan_in_days):
        """
        Using the OpenSky Network API it tracks the flights from and to specific airports.
        """
        self.traffic_timespan_in_days = traffic_timespan_in_days
        self.client: OpenskyNetworkClient = OpenskyNetworkClient.create('opensky-network.org', timeout=30)

    def _flight_connections_today(self, icao: str, callback: Callable) -> List[FlightConnection]:
        """
        Returns the flight connections (arrivals or departures based on the callback) of the current day.

        :param icao: airport identifier
        """
        begin, end = self._days_span(self.traffic_timespan_in_days)

        try:
            result = callback(icao, begin, end)
        except Exception as e:
            _logger.error(str(e))
            result = []

        return result

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def _arrivals_today_handler(self, icao: str) -> List[FlightConnection]:
        """
        Returns the flight arrivals of the current day.

        The result is cached for 10 minutes (could be more) as the flight arrivals do not change so often within a day

        :param icao: airport identifier
        """
        return self._flight_connections_today(icao, callback=self.client.get_flight_arrivals)

    @cached(cache=TTLCache(maxsize=1024, ttl=600))
    def _departures_today_handler(self, icao: str) -> List[FlightConnection]:
        """
        Returns the flight departures of the current day.

        The result is cached for 10 minutes (could be more) as the flight departures do not change so often within a day

        :param icao: airport identifier
        """
        return self._flight_connections_today(icao, callback=self.client.get_flight_departures)

    def _get_states(self) -> List[StateVector]:
        """
        Returns the current list of flight states
        """
        try:
            states = self.client.get_states()
            result = states.states
        except Exception as e:
            _logger.error(str(e))
            result = []

        return result

    @cached(cache=TTLCache(maxsize=1024, ttl=30))
    def get_states_dict(self, context: Optional[Any] = None) -> Dict[str, StateVector]:
        """
        """
        states = self._get_states()

        return {state.icao24: state for state in states}

    def arrivals_handler(self, airport: str, context: Optional[Any] = None) -> Message:
        """
        Is the callback that will be used to the arrival related topics
        """
        states_dict = self.get_states_dict()

        data = self._flight_connection_handler(airport,
                                               states_dict=states_dict,
                                               get_flight_connections_handler=self._arrivals_today_handler)

        return Message(body=json.dumps(data), content_type='application/json')

    def departures_handler(self, airport: str, context: Optional[Any] = None) -> Message:
        """
        Is the callback that will be used to the departure related topics
        """
        states_dict = self.get_states_dict()

        data = self._flight_connection_handler(airport,
                                               states_dict=states_dict,
                                               get_flight_connections_handler=self._departures_today_handler)

        return Message(body=json.dumps(data), content_type='application/json')

    def _flight_connection_handler(self,
                                   airport: str,
                                   states_dict: Dict[str, StateVector],
                                   get_flight_connections_handler: Callable) -> List[AirTrafficDataType]:
        """
        Matches the flight connections (arrivals or departures of the airport depending on the provided handler) with
        the current states (flights on going) and returns a subset of the data of those flights.
        :param airport: icao of the airport
        :param states_dict:
        :param get_flight_connections_handler:
        :return:
        """
        flight_connections = get_flight_connections_handler(airport)

        flight_connections_dict = {fc.icao24: fc for fc in flight_connections if fc.icao24}

        flight_connections_with_state = {icao24: fc for icao24, fc in flight_connections_dict.items()
                                         if icao24 in states_dict}

        data = [self._get_flight_data(states_dict.get(fc_icao24), fc)
                for fc_icao24, fc in flight_connections_with_state.items()]

        return data

    @staticmethod
    def _get_flight_data(state: StateVector, flight_connection: FlightConnection) -> AirTrafficDataType:
        """
        Combines data of an ongoing flight and an arrival or departure and returns a subset of it.
        :param state:
        :param flight_connection:
        :return:
        """
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

    @staticmethod
    def _days_span(days: int) -> Tuple[int, int]:
        """
        Returns the timestamps of the start (00:00:00 AM) and the end (23:59:59 PM) of the current day in seconds since
        UNIX epoch.
        :param days: indicates how many days in the past from today the span will be calculated
        :return:
        """
        end = datetime.today()
        begin = end - timedelta(days=days)

        return int(begin.timestamp()), int(end.timestamp())
