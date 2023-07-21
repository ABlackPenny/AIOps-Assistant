# Start your image with a Python base image
# THIS NEED TO BE CHANGED i GUESS
# TODO
FROM python:3.9-buster

# The /app directory should act as the main application directory
WORKDIR /application

# Copy the requirements.txt file
COPY ./assistant/requirements.txt ./requirements.txt

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev

# Upgrade pip and install aiohttp
RUN pip install --upgrade pip
RUN pip install aiohttp

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy local directories to the current local directory of our docker image (/app)
COPY ./assistant/assistant.py ./assistant/
COPY ./assistant/models/openai_gpt.py ./models/
COPY ./assistant/integrations/probe_mysql.py ./probe_mysql/
COPY ./assistant/probes/controller.py ./controller/
COPY ./assistant/probes/database.py ./database/

EXPOSE 3000

# Start the app
CMD ["python", "./assistant/assistant.py"]
