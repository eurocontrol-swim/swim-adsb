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
from functools import partial

from swim_pubsub.core.factory import AppFactory
from swim_pubsub.core.handlers import Topic

from swim_adsb.adsb.traffic import OpenSkyNetworkDataHandler

__author__ = "EUROCONTROL (SWIM)"


if __name__ == '__main__':
    app = AppFactory.create_publisher_app_from_config('config.yml')
    # cities = app.config['ADSB']['CITIES']

    cities = {
        'Brussels': 'EBBR',
        'Amsterdam': 'EHAM',
        'Paris': 'LFPG',
        'Berlin': 'EDDB',
        'Athens': 'LGAV'
    }

    opensky = OpenSkyNetworkDataHandler()

    flights = Topic(name='flights', interval=5, handler=opensky.get_states_dict)

    for city, code in cities.items():
        arrivals_handler = partial(opensky.arrivals_handler, code)
        departures_handler = partial(opensky.departures_handler, code)

        flights.add_route(key=f"arrivals.{city.lower()}", handler=arrivals_handler)
        flights.add_route(key=f"departures.{city.lower()}", handler=departures_handler)

    publisher = app.register_publisher('test', 'test')
    publisher.register_topic(flights)

    app.run()
