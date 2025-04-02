# Use official Python image as base
FROM python:latest

# Set working directory
WORKDIR /home/work

# Install required packages
RUN pip install --upgrade pip && \
    pip install notion-client
