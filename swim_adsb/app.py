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
import logging
import os
from functools import partial

from swim_pubsub.core.topics.topics import ScheduledTopic, Pipeline
from swim_pubsub.publisher import PubApp

from swim_adsb.adsb.air_traffic import AirTraffic

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


def _get_config_path():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'config.yml')


def create_app():
    # instantiate app
    return PubApp.create_from_config(_get_config_path())


app = create_app()

publisher = app.register_publisher(username=app.config['SWIM_ADSB_SM_USER'],
                                   password=app.config['SWIM_ADSB_SM_PASS'])

config = app.config['ADSB']

# configure topics
air_traffic = AirTraffic(traffic_timespan_in_days=config['TRAFFIC_TIMESPAN_IN_DAYS'])

for city, code in config['CITIES'].items():
    arrivals_pipeline = Pipeline([air_traffic.get_states_dict,
                                  partial(air_traffic.arrivals_handler, code)])

    departures_pipeline = Pipeline([air_traffic.get_states_dict,
                                    partial(air_traffic.departures_handler, code)])

    arrivals_topic = ScheduledTopic(topic_id=f"arrivals.{city.lower()}",
                                    pipeline=arrivals_pipeline,
                                    interval_in_sec=config['INTERVAL_IN_SEC'])
    departures_topic = ScheduledTopic(topic_id=f"departures.{city.lower()}",
                                      pipeline=departures_pipeline,
                                      interval_in_sec=config['INTERVAL_IN_SEC'])

    publisher.register_topic(arrivals_topic)
    publisher.register_topic(departures_topic)

if __name__ == '__main__':
    app.run()
