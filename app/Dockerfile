FROM python:3.10


######## INSTALLING SUPERCRONIC ########
# Install supercronic
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=71b0d58cc53f6bd72cf2f293e09e294b79c666d8 \
    SUPERCRONIC=supercronic-linux-amd64

RUN curl -fsSLO "$SUPERCRONIC_URL" \
    && echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - \
    && chmod +x "$SUPERCRONIC" \
    && mv "$SUPERCRONIC" "/usr/local/bin/${SUPERCRONIC}" \
    && ln -s "/usr/local/bin/${SUPERCRONIC}" /usr/local/bin/supercronic

######## INSTALLING CDF UTILITIES ########
# Set the working directory for the build
WORKDIR /opt
# Download, extract, and compile the CDF utilities
RUN wget https://spdf.gsfc.nasa.gov/pub/software/cdf/dist/cdf39_1/linux/cdf39_1-dist-cdf.tar.gz && \
    tar -xvf cdf39_1-dist-cdf.tar.gz && \
    rm cdf39_1-dist-cdf.tar.gz && \
    cd cdf39_1-dist && \
    make OS=linux ENV=gnu all
# Add the CDF utilities to the CDF_LIB
ENV CDF_LIB="/opt/cdf39_1-dist/src/lib"

######## DEPLOYING THE CODE ########
# Set the working directory in the container
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the script on startup and then start the cron service
CMD ["/usr/local/bin/supercronic", "-passthrough-logs", "/app/scripts/app_job.cron"]
