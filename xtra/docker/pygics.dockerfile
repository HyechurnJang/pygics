FROM python:3

COPY ./pygics /usr/bin/pygics
RUN chmod 755 /usr/bin/pygics
RUN mkdir -p /pygics
RUN pip install --no-cache-dir pygics
WORKDIR /pygics
CMD ["/usr/bin/pygics"]