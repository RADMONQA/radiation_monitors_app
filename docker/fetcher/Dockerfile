# Use the minimal Alpine image as the base
FROM alpine:latest

# Install cron, wget, and grep in the Alpine container
RUN apk update && apk add --no-cache wget grep

# Set the working directory in the container
WORKDIR /app

# Copy the entire directory with scripts from the host to the container
COPY ./scripts /app/scripts

# Set permissions for the script directory
RUN chmod -R +x /app/scripts

# Copy the cron job file into the container
COPY fetcher_job /etc/cron.d/fetcher_job

# Give execution rights on the cron job file
RUN chmod 0644 /etc/cron.d/fetcher_job

# Apply the cron job
RUN crontab /etc/cron.d/fetcher_job

# Expose a volume to be shared with other containers
VOLUME /radem_data

# Command to run the script on startup and then start the cron service
CMD /app/scripts/fetch_all.sh 2>&1 \
    && crond -f
