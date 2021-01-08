FROM golang:alpine
RUN mkdir /app
WORKDIR /app
ADD ./bin/main main
ADD ./public/ public/
RUN chmod +x ./main
CMD ["./main"]
