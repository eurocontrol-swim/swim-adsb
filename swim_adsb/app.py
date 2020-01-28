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
from typing import Union, Dict, Any

import yaml
from pkg_resources import resource_filename
from pubsub_facades.swim_pubsub import SWIMPublisher

from swim_adsb.adsb.air_traffic import AirTraffic

__author__ = "EUROCONTROL (SWIM)"

_logger = logging.getLogger(__name__)


def _get_config_path():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'config.yml')


def _from_yaml(filename: str) -> Union[Dict[str, Any], None]:
    """
    Converts a YAML file into a Python dict

    :param filename:
    :return:
    """
    if not filename.endswith(".yml"):
        raise ValueError("YAML config files should end with '.yml' extension (RTFMG).")

    with open(filename) as f:
        obj = yaml.load(f, Loader=yaml.FullLoader)

    return obj or None


config = _from_yaml(filename=resource_filename(__name__, 'config.yml'))

# The publisher that will communicate with the SubscriptionManager to create new topics and with the broker where the
# messages will be routed
swim_publisher = SWIMPublisher.create_from_config(_get_config_path())


# configure topics
air_traffic = AirTraffic(traffic_timespan_in_days=config['ADSB']['TRAFFIC_TIMESPAN_IN_DAYS'])
interval_in_sec = config['ADSB']['INTERVAL_IN_SEC']

for city, code in config['ADSB']['CITIES'].items():
    swim_publisher.add_topic(topic_name=f"arrivals.{city.lower()}",
                             message_producer=partial(air_traffic.arrivals_handler, code),
                             interval_in_sec=interval_in_sec)

    swim_publisher.add_topic(topic_name=f"departures.{city.lower()}",
                             message_producer=partial(air_traffic.arrivals_handler, code),
                             interval_in_sec=interval_in_sec)


if __name__ == '__main__':
    swim_publisher.run()
