FROM swim-base

LABEL maintainer="SWIM EUROCONTROL <http://www.eurocontrol.int>"

ENV PATH="/opt/conda/bin:$PATH"

RUN mkdir -p /app
WORKDIR /app

COPY requirements_pip.txt requirements_pip.txt
RUN pip3 install -r requirements_pip.txt

COPY ./swim_adsb/ ./swim_adsb

COPY . /source/
RUN set -x \
    && pip3 install /source \
    && rm -rf /source

CMD ["python", "/app/swim_adsb/app.py"]
