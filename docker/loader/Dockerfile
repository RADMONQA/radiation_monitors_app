
FROM python:3.10

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

# Set the working directory in the container
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the entire directory with scripts from the host to the container
COPY ./scripts /app/scripts

# Set permissions for the script directory
RUN chmod -R +x /app/scripts

# CMD /app/scripts/load_to_influxdb.sh

CMD /app/scripts/3_processing_line_protocol.py



# # Copy the cron job file into the container
# COPY fetcher_job /etc/cron.d/fetcher_job

# # Give execution rights on the cron job file
# RUN chmod 0644 /etc/cron.d/fetcher_job

# # Apply the cron job
# RUN crontab /etc/cron.d/fetcher_job

# # Create the log file to be accessible by cron
# RUN touch /var/log/fetcher.log

# # Expose a volume to be shared with other containers
# VOLUME /radem_data

# # Command to run the script on startup and then start the cron service
# CMD /app/scripts/fetch_all.sh >> /var/log/fetcher.log 2>&1 && crond -f
