#!/usr/bin/env python3
"""
Load parquet files into PostgreSQL database using psql COPY command
"""
import pandas as pd
import sqlalchemy as sa
from pathlib import Path
import glob
import time
import sys
import subprocess
import os
import tempfile

def wait_for_postgres(host="postgres", port=5432, max_attempts=30):
    """Wait for PostgreSQL to be ready"""
    for i in range(max_attempts):
        try:
            # Try to connect with psql
            result = subprocess.run(
                ["pg_isready", "-h", host, "-p", str(port), "-U", "admin"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("PostgreSQL is ready!")
                return True
        except Exception as e:
            pass
        
        if i == 0:
            print("Waiting for PostgreSQL to be ready...")
        time.sleep(2)
    print("Failed to connect to PostgreSQL")
    return False

def pandas_to_postgres_type(pandas_dtype):
    """Convert pandas dtype to PostgreSQL type"""
    dtype_str = str(pandas_dtype)
    
    # Integer types
    if 'int' in dtype_str:
        if 'int64' in dtype_str:
            return 'BIGINT'
        elif 'int32' in dtype_str:
            return 'INTEGER'
        elif 'int16' in dtype_str or 'int8' in dtype_str:
            return 'SMALLINT'
        else:
            return 'BIGINT'
    
    # Float types
    elif 'float' in dtype_str:
        if 'float64' in dtype_str:
            return 'DOUBLE PRECISION'
        elif 'float32' in dtype_str:
            return 'REAL'
        else:
            return 'DOUBLE PRECISION'
    
    # Boolean
    elif 'bool' in dtype_str:
        return 'BOOLEAN'
    
    # DateTime types
    elif 'datetime' in dtype_str or 'timestamp' in dtype_str:
        return 'TIMESTAMP'
    
    # Date
    elif 'date' in dtype_str:
        return 'DATE'
    
    # Time
    elif 'time' in dtype_str:
        return 'TIME'
    
    # String/Object types
    else:
        return 'TEXT'

def load_parquet_files():
    """Load all parquet files into PostgreSQL using psql COPY"""
    
    if not wait_for_postgres():
        sys.exit(1)
    
    # Set PGPASSWORD environment variable
    os.environ['PGPASSWORD'] = 'admin'
    
    # Create schema using psql
    print("Creating schema...")
    subprocess.run([
        "psql", "-h", "postgres", "-U", "admin", "-d", "data",
        "-c", "CREATE SCHEMA IF NOT EXISTS taxidata;"
    ], check=True)
    
    # Drop all existing tables in the taxidata schema
    print("Dropping all existing tables in taxidata schema...")
    drop_tables_cmd = """
    DROP TABLE IF EXISTS taxidata.yellow_tripdata_2025_01 CASCADE;
    DROP TABLE IF EXISTS taxidata.yellow_tripdata_2025_02 CASCADE;
    DROP TABLE IF EXISTS taxidata.yellow_tripdata_2025_03 CASCADE;
    """
    subprocess.run([
        "psql", "-h", "postgres", "-U", "admin", "-d", "data",
        "-c", drop_tables_cmd
    ], check=False)  # Don't fail if tables don't exist
    
    # Load parquet files
    parquet_files = glob.glob('/app/taxi-data/*.parquet')
    
    if not parquet_files:
        print("No parquet files found in /app/taxi-data/")
        return
    
    for file_path in sorted(parquet_files):
        # Postgres does not allow dashes in table names so we replace them with underscores
        table_name = Path(file_path).stem.replace('-', '_')
        print(f"Loading {table_name}...")
        
        try:
            # Read parquet file
            df = pd.read_parquet(file_path)
            
            # Create CSV in temporary location
            # Handle NULL values and ensure proper date/datetime formatting
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                csv_path = tmp_file.name
                # Replace NaN/NaT with empty strings for PostgreSQL NULL handling
                df_to_write = df.copy()
                for col in df_to_write.columns:
                    if df_to_write[col].isna().any():
                        df_to_write[col] = df_to_write[col].replace({pd.NA: None, pd.NaT: None})
                
                df_to_write.to_csv(csv_path, index=False, header=True, na_rep='')
            
            # Create table using psql with correct datatypes
            print(f"  Creating table {table_name}...")
            # Map pandas dtypes to PostgreSQL types
            column_definitions = []
            for col in df.columns:
                pg_type = pandas_to_postgres_type(df[col].dtype)
                column_definitions.append(f'"{col}" {pg_type}')
            
            create_table_cmd = f"""
            CREATE TABLE taxidata.{table_name} ({','.join(column_definitions)});
            """
            
            subprocess.run([
                "psql", "-h", "postgres", "-U", "admin", "-d", "data",
                "-c", create_table_cmd
            ], check=True)
            
            # Copy CSV data to PostgreSQL using psql COPY
            print(f"  Copying data to {table_name}...")
            copy_cmd = f"\\COPY taxidata.{table_name} FROM '{csv_path}' WITH (FORMAT CSV, HEADER true)"
            
            subprocess.run([
                "psql", "-h", "postgres", "-U", "admin", "-d", "data",
                "-c", copy_cmd
            ], check=True)
            
            # Clean up temp file
            os.unlink(csv_path)
            
            print(f"✓ Loaded {table_name} ({len(df)} rows)")
        except Exception as e:
            print(f"✗ Error loading {table_name}: {e}")
            if 'csv_path' in locals():
                try:
                    os.unlink(csv_path)
                except:
                    pass

if __name__ == "__main__":
    load_parquet_files()
