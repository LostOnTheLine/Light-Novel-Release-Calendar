FROM alpine/git:latest
WORKDIR /app
COPY pusher.sh .
RUN apk add --no-cache jq
RUN chmod +x pusher.sh
# ENTRYPOINT ["/bin/sh"]
# CMD ["/app/pusher.sh"]
CMD ["./pusher.sh"]