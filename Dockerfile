FROM ubuntu:16.04
ENV LC_ALL=C.UTF-8

# Install packages additional Ubuntu PPAs.
RUN apt-get update -y && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository -y ppa:ubuntugis/ppa

# Install needed binary packages for pip installation and spatial requirements
RUN apt-get update -y && \
    apt-get install -y libsm6 libxext6 curl python-pip && \
    apt-get install -y python-cairo libgeos-c1v5 libgdal20 python-gdal \
        python-pip python-dev libpq-dev memcached libffi-dev gdal-bin libgdal-dev

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get update -y && \
    apt-get install -y nodejs

COPY inceptionV3      /usr/local/src/roadclassifier/inceptionV3
COPY mnist            /usr/local/src/roadclassifier/mnist
COPY src              /usr/local/src/roadclassifier/src
COPY static           /usr/local/src/roadclassifier/static
COPY submodules       /usr/local/src/roadclassifier/submodules
COPY app.json         /usr/local/src/roadclassifier
COPY gulpfile.js      /usr/local/src/roadclassifier
COPY main.py          /usr/local/src/roadclassifier
COPY package.json     /usr/local/src/roadclassifier
COPY templates        /usr/local/src/roadclassifier/templates
COPY requirements.txt /usr/local/src/roadclassifier
RUN cd /usr/local/src/roadclassifier && \
    pip install -Ur requirements.txt

WORKDIR /usr/local/src/roadclassifier

RUN npm install

# mount-point for persistence beyond container
VOLUME ["/data"]
EXPOSE 5000

CMD gunicorn -w4 -b 0.0.0.0:5000 main:app --log-file=-