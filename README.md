# SWIM ADSB

SWIM ADSB is an application that retrieves live air traffic information from 
[OpenSky Network](https://opensky-network.org/) and demonstrates how it can use the 
[SWIM-PubSub](https://bitbucket.org/antavelos-eurocontrol/swim-pubsub) mini framework in order to publish this
information through a broker.


## Configuration
Besides the default `swim-pubsub` configuration that is required you can also configure the cities you wish
to monitor the flight data from as well as how often you want this information to be refreshed. Example:

```yml
ADSB:
  CITIES:
    Brussels: 'EBBR'
    Amsterdam: 'EHAM'
    Paris: 'LFPG'
    Berlin: 'EDDB'
    Athens: 'LGAV'
  INTERVAL_IN_SEC: 5
```

## Run
In order to run the application you need first to create and activate a conda environment. The required 
packages can be found in `requirements.txt`.

```shell
conda env create --name swim-adsb -f requirements.yml
source activate swim-adsb
python app.py
```

## Data
The data produced comes as a list of dictionaries for each flight with the following keys:
```python
[
    {
        'icao24': '4691c7',         # the trasponder identifier of the aircraft
        'lat': 41.8699,             # the latitude of the aircraft
        'lng': 12.2514,             # the longitude of the aircraft
        'from': 'LGAV',             # the origin airport
        'to': 'LIRF',               # the destination airport
        'last_contact': 1560869065  # the timestamp of the last contact in seconds since UNIX epoch
    }
]
```