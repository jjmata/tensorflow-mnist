FROM ubuntu:16.04
ENV LC_ALL=C.UTF-8

# Install packages additional Ubuntu PPAs.
RUN apt-get update -y && \
    apt-get install -y software-properties-common python-software-properties && \
    add-apt-repository -y ppa:ubuntugis/ppa

# Install needed binary packages for pip installation and spatial requirements
RUN apt-get update -y && \
    apt-get install -y libsm6 libxext6 python-pip && \
    apt-get install -y python-cairo libgeos-c1v5 libgdal20 python-gdal \
        python-pip python-dev libpq-dev memcached libffi-dev gdal-bin libgdal-dev

COPY . /usr/local/src/roadclassifier
RUN cd /usr/local/src/roadclassifier && \
    pip install -Ur requirements.txt

# mount-point for persistence beyond container
VOLUME ["/data"]

WORKDIR /usr/local/src/roadclassifier