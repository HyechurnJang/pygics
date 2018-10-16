FROM ubuntu:latest

COPY ./pygics /usr/bin/pygics
RUN chmod 755 /usr/bin/pygics
RUN mkdir -p /opt/pygics /opt/pygics/workspace
RUN apt update && apt install -y python3-venv
RUN python3 -m venv /opt/pygics/pygenv
RUN . /opt/pygics/pygenv/bin/activate && pip install --upgrade pip && deactivate
RUN . /opt/pygics/pygenv/bin/activate && pip install --no-cache-dir pygics && deactivate
WORKDIR /opt/pygics/workspace
CMD ["/usr/bin/pygics"]