FROM alpine:latest
LABEL authors="sagilyp"

RUN apk add --no-cache g++ git musl-dev libgomp
RUN git clone https://github.com/sagilyp/PAPHSD.git /app

WORKDIR /app

RUN g++ -fopenmp lab1/main.cpp -o cpu_load

CMD ["./cpu_load"]