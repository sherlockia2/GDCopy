FROM ubuntu:latest

WORKDIR /usr/src/app

# Set Environment
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN DEBIAN_FRONTEND="noninteractive"
RUN chmod 777 /usr/src/app && apt-get -qq update && apt upgrade -y && apt-get -qq install python3 python3-pip software-properties-common

#Updating Libraries
RUN pip3 install -U pip
COPY requirements.txt .
RUN pip3 install --no-cache-dir -U -r requirements.txt

#Copying All Source
COPY . .

#Starting Bot
RUN chmod +x start.sh
CMD ["bash", "start.sh"]
