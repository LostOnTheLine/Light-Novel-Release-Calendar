FROM alpine/git

WORKDIR /app
COPY pusher.sh .
RUN chmod +x pusher.sh

ENTRYPOINT ["/bin/sh"]
CMD ["/app/pusher.sh"]