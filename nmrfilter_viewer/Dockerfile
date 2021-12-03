FROM continuumio/miniconda:latest
MAINTAINER Ricardo R. da Silva <ridasilva@usp.br>

ENV INSTALL_PATH /home/nmrfilter
RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH

COPY environment.yml environment.yml
RUN conda env create -f environment.yml
RUN echo "source activate nmrfilter" > ~/.bashrc
ENV PATH /opt/conda/envs/nmrfilter/bin:$PATH

RUN conda install -y -c cidermole jdk8

COPY . /home/nmrfilter
RUN git clone https://github.com/stefhk3/nmrfilter.git
RUN mv nmrfilter /home/nmrfilter/api

EXPOSE 5040
CMD sh /home/nmrfilter/run_server.sh 
