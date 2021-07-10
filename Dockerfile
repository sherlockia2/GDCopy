FROM ubuntu:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

RUN DEBIAN_FRONTEND="noninteractive" apt-get -qq install python3 python3-pip software-properties-common

RUN  apt-get -qq update \
  && apt-get install -y wget \
  && apt install unzip \
  && rm -rf /var/lib/apt/lists/*

#Updating Libraries
RUN pip3 install -U pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U -r requirements.txt

#Copying All Source
COPY . .

#Starting Bot
CMD ["bash", "start.sh"]
