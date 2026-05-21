FROM ubuntu:noble-20251013@sha256:c35e29c9450151419d9448b0fd75374fec4fff364a27f176fb458d472dfc9e54

# setup environment
RUN apt update -y && \
    apt clean

WORKDIR /xilriws

ENV DEBIAN_FRONTEND=noninteractive

RUN apt install -y software-properties-common
RUN apt update && apt install -y python3 python3-venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
RUN pip install --upgrade pip==25.0.1
RUN pip install uv==0.11.7

# install chromium dependencies
# from https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/blob/master/docker/build.Dockerfile
RUN apt-get -y install wget bison debhelper desktop-file-utils flex gperf gsettings-desktop-schemas-dev imagemagick \
  libasound2-dev libavcodec-dev libavformat-dev libavutil-dev libcap-dev libcups2-dev libcurl4-openssl-dev libdrm-dev \
  libegl1-mesa-dev libelf-dev libevent-dev libexif-dev libflac-dev libgbm-dev libgcrypt20-dev libgl1-mesa-dev libgles2-mesa-dev \
  libglew-dev libglib2.0-dev libglu1-mesa-dev libgtk-3-dev libhunspell-dev libjpeg-dev libjs-jquery-flot libjsoncpp-dev \
  libkrb5-dev liblcms2-dev libminizip-dev libmodpbase64-dev libnspr4-dev libnss3-dev libopenjp2-7-dev libopus-dev libpam0g-dev \
  libpci-dev libpipewire-0.3-dev libpng-dev libpulse-dev libre2-dev libsnappy-dev libspeechd-dev libudev-dev libusb-1.0-0-dev \
  libva-dev libvpx-dev libwebp-dev libx11-xcb-dev libxcb-dri3-dev libxshmfence-dev libxslt1-dev libxss-dev libxt-dev libxtst-dev\
  mesa-common-dev ninja-build pkg-config python3-jinja2 python3-setuptools python3-xcbgen python-is-python3 qtbase5-dev \
  uuid-dev valgrind wdiff x11-apps xcb-proto xfonts-base xvfb xz-utils yasm

# install chromium
RUN wget -O chromium.tar.xz https://github.com/ungoogled-software/ungoogled-chromium-portablelinux/releases/download/146.0.7680.177-1/ungoogled-chromium-146.0.7680.177-1-x86_64_linux.tar.xz
RUN mkdir chromium_install \
    && tar -xf chromium.tar.xz -C chromium_install/ \
    && mkdir chromium \
    && mv chromium_install/*/* chromium \
    && rm chromium.tar.xz

# install Xilriws dependencies
COPY . .
RUN uv sync --frozen --no-install-project

ARG ENTRYPOINT_SCRIPT=app.py
ENV ENTRYPOINT_SCRIPT=${ENTRYPOINT_SCRIPT}
ENTRYPOINT ["sh", "-c", "exec uv run --frozen python \"$ENTRYPOINT_SCRIPT\""]
