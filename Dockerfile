# Create this docker file based off a Python 3.9 Linux image
FROM python:3.9-slim-buster

# Run everything from /app
WORKDIR /app

# Copy over the files
COPY requirements.txt requirements.txt
COPY app.py app.py
COPY dev_to.py dev_to.py
COPY github_access.py github_access.py
COPY entrypoint.sh entrypoint.sh

# Install the Python requirements
RUN pip3 install -r requirements.txt

# Execute the shell script as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
