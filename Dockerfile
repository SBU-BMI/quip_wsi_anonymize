FROM python:2.7.17-slim
MAINTAINER Tahsin Kurc

RUN apt-get -q update && \
	apt-get install -y openslide-tools build-essential git && \
	pip install openslide-python pandas

WORKDIR /root

COPY . /root/.
RUN git clone https://github.com/bgilbert/anonymize-slide.git  && \
	chmod 0755 slide_anonymize

ENV PATH=.:$PATH:/root/

CMD ["slide_anonymize"]

