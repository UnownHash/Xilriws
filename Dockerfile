FROM ubuntu:latest
RUN apt update -y && \
    apt clean

WORKDIR /xilriws

ENV DEBIAN_FRONTEND noninteractive
#RUN apt install -y git-all
#RUN git clone https://github.com/UnownHash/Xilriws-Public
#RUN cp -r Xilriws-Public/xilriws-fingerprint-random /xilriws/xilriws-fingerprint-random
#RUN cp -r Xilriws-Public/xilriws-cookie-delete /xilriws/xilriws-cookie-delete
#RUN cp -r Xilriws-Public/xilriws-proxy /xilriws/xilriws-proxy
#RUN cp -r Xilriws-Public/xilriws-targetfp /xilriws/xilriws-targetfp

RUN apt install -y software-properties-common
RUN apt update && apt install -y python3 python3-venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip==25.0.1
RUN pip install poetry

RUN apt install -y wget

RUN wget -q -O - https://github.com/NDViet/google-chrome-stable/releases/download/125.0.6422.141-1/google-chrome-stable_125.0.6422.141-1_amd64.deb > ./chrome.deb
RUN apt install -y ./chrome.deb
RUN rm ./chrome.deb

#RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub > linux_signing_key.pub
#RUN install -D -o root -g root -m 644 linux_signing_key.pub /etc/apt/keyrings/linux_signing_key.pub
#RUN sh -c 'echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/linux_signing_key.pub] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'
#RUN apt update -y
#RUN apt install -y google-chrome-stable

#RUN apt install -y curl
#RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
#RUN echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main"| tee /etc/apt/sources.list.d/brave-browser-release.list
#RUN apt update -y
#RUN apt install -y brave-browser

COPY . .
RUN poetry install --no-root

ENTRYPOINT ["poetry", "run", "python", "app.py"]
