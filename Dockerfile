FROM python:3.12-slim

# Install system dependencies including PostgreSQL client
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python packages with all dependencies
RUN pip install --no-cache-dir \
    great_expectations \
    'great_expectations[postgresql]' \
    jupyter \
    pandas \
    pyarrow \
    psycopg2-binary \
    sqlalchemy \
    ipykernel

# Copy parquet files
COPY taxi-data/*.parquet /app/taxi-data/

# Copy data loading script
COPY load_data.py /app/load_data.py

# Expose Jupyter port and data docs port
EXPOSE 8888 8080

# Set working directory for Jupyter
WORKDIR /root/code/gxtutorial

# Default command - start Jupyter from the notebook directory
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]
