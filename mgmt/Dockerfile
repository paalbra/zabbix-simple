FROM debian:latest

RUN apt-get update && \
    apt-get install -y openssl && \
    apt-get autoremove -y && \
    apt-get autoclean

WORKDIR /mgmt

COPY entrypoint.sh .

ENTRYPOINT ["/bin/bash"]
CMD ["entrypoint.sh", "init"]
