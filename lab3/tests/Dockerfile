FROM alpine:latest

RUN apk update && apk add \
        curl \
        jq \
        parallel \
        bash \
        dos2unix

WORKDIR /app

COPY send_requests.sh /app/send_requests.sh

RUN dos2unix /app/send_requests.sh
RUN chmod +x /app/send_requests.sh

COPY users.json /app/users.json

CMD ["sh", "-c", "/app/send_requests.sh && tail -f /dev/null"]
