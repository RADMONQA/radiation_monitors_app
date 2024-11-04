FROM python:3.10


######## INSTALLING DEPENDENCIES ########
# Install cron using apt
RUN apt-get update && \
    apt-get install -y cron


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


######## SETTING UP THE CRON ########
# Copy the cron job file into the container and set permissions
COPY app_job /etc/cron.d/app_job
# Give execution rights on the cron job file and apply the cron job
RUN chmod 0644 /etc/cron.d/app_job && \
    crontab /etc/cron.d/app_job


# Run the script on startup and then start the cron service
CMD /app/scripts/fetch_and_publish.sh 2>&1 \
    && cron -f