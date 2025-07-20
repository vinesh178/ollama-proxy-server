FROM python:3.9-slim

WORKDIR /app

COPY simple_ollama_proxy.py .

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "simple_ollama_proxy.py"]