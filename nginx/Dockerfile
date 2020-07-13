FROM ubuntu:20.04

RUN apt update -qq
RUN apt install -y less vim g++ wget make nginx-full \
        libnginx-mod-rtmp
RUN apt install -y -qq build-essential libpcre3 libpcre3-dev libssl-dev
CMD ["nginx", "-g", "daemon off;"]
