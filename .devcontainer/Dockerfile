FROM mcr.microsoft.com/devcontainers/python:3.11-bookworm

# Install Node.js for React frontend
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install MySQL client tooling
RUN apt-get update && apt-get install -y default-mysql-client