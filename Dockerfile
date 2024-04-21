FROM python:3.12

RUN mkdir /workspace
WORKDIR /workspace

RUN curl -Lo /tmp/cloudquery https://github.com/cloudquery/cloudquery/releases/download/cli-v3.5.1/cloudquery_linux_amd64 \
    && chmod a+x /tmp/cloudquery \
    && mv /tmp/cloudquery /usr/bin/cloudquery

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
RUN cd /tmp \
    && unzip awscliv2.zip\
    && ./aws/install

ADD ./requirements.txt .
RUN python -m pip install -r requirements.txt
RUN rm ./requirements.txt

ADD ./llmt /workspace/llmt
ADD ./examples/simple.py /workspace/simple.py
ADD ./examples/chat.py /workspace/chat.py

ENTRYPOINT ["python"]
