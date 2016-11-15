FROM nvidia/cuda:8.0-cudnn5-devel

# system setup and package installation for caffe
RUN rm /bin/sh \
 && ln -s /bin/bash /bin/sh \
 && apt-get -y update \
 && apt-get -y install git cmake curl wget \
                       libatlas-base-dev libatlas-dev \
                       libboost1.55-all-dev \
                       libprotobuf-dev protobuf-compiler \
                       libgoogle-glog-dev libgflags-dev \
                       libhdf5-dev \
                       libopencv-dev \
                       liblmdb-dev \
                       libleveldb-dev \
                       libsnappy-dev

# package installation for TattDL
RUN apt-get -y install python-setuptools cython python-numpy python-opencv python-pip \
                       python-skimage python-protobuf python-yaml
RUN pip install easydict

# install git-lfs
RUN curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash
RUN apt-get install -y git-lfs

# get TattDL
RUN git clone --recursive --branch wip/remove-detector-matplotlib-use https://github.com/memex-explorer/TattDL.git

WORKDIR /TattDL/lib
RUN make

WORKDIR /TattDL/caffe-fast-rcnn

# enable linking python bindings for caffe
RUN sed 's/# WITH_PYTHON_LAYER := 1/WITH_PYTHON_LAYER := 1/' Makefile.config.example > Makefile.config

# compile caffe
RUN make && make pycaffe

WORKDIR /TattDL/data/scripts
RUN ./fetch_faster_rcnn_models.sh && ./fetch_faster_rcnn_models.sh # this should be run twice
RUN git lfs pull
