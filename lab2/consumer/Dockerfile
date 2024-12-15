# Use the official debian image as the base image
FROM debian:12

# Set the working directory inside the container
WORKDIR /app

# Copy the consumer.cpp, crow_all.h, and json.hpp files to the working directory
COPY consumer.cpp .
COPY crow_all.h .
COPY json.hpp .

# Install Boost dependencies
RUN apt-get update && \
    apt-get install -y build-essential && \
    apt-get install -y libboost-all-dev

# Compile the consumer.cpp file
RUN g++ -lpthread -o consumer consumer.cpp

CMD ["cd /app"]

# Set the entry point for the container
CMD ["./consumer"]
