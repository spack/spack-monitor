FROM bitnami/minideb:buster
ENV PYTHONUNBUFFERED 1
ENV PATH /opt/conda/bin:${PATH}
ENV LANG C.UTF-8
ENV SHELL /bin/bash
RUN install_packages wget curl bzip2 ca-certificates openssl gnupg2 git vim python3-pygraphviz gcc pkg-config
COPY requirements.txt /requirements.txt
RUN /bin/bash -c "curl -L https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh"
RUN /bin/bash -c "conda install -y -c conda-forge mamba && \
    mamba create -q -y -c conda-forge -n shub && \
    source activate shub && \
    conda install -c conda-forge uwsgi xmlsec && \
    pip install --upgrade pip wheel && \
    pip install -r requirements.txt && \
    conda clean --all -y && \
    which python"
RUN echo "source activate shub" > ~/.bashrc
ENV PATH /opt/conda/envs/shub/bin:${PATH}

RUN apt-get autoremove -y && apt-get clean
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /code
ADD . /code/
CMD /code/run_uwsgi.sh

EXPOSE 3031
