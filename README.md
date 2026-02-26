# Great Expectations (GX) Core Tutorial Environment

This Docker setup provides a complete environment for working with Great Expectations, including Jupyter notebooks, PostgreSQL database, and sample taxi data.

## Features

- Python 3.12 environment
- Great Expectations installed with all dependencies
- Jupyter notebooks
- Pandas for data manipulation
- PostgreSQL database with taxi data pre-loaded
- Pre-configured tutorial directory and notebook

## Quick Start

0. **Open a terminal and cd into the correct dictory where the Dockerfile is located:**
   ```bash
   cd ~/path/to/repository
   ```

1. **Build and start the containers:**
   ```bash
   docker compose up --build
   ```

2. **Access Jupyter Notebook:**
   - Open your browser to `http://localhost:8888`
   - The notebook `gxtutorial.ipynb` will be in the `/root/code/gxtutorial` directory

3. **Access PostgreSQL:**
   - Host: localhost
   - Port: 5432
   - Database: data
   - Username: admin
   - Password: admin
   - Schema: taxidata

## Data

The taxi data from `https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page` is loaded into the following tables in the `taxidata` schema:
- `yellow_tripdata_2025-01`
- `yellow_tripdata_2025-02`
- `yellow_tripdata_2025-03` (this file has been modified for the purpose of this tutorial)


## Stopping the Containers

```bash
docker compose down
```

To remove all data (including the database and volumes):
```bash
docker compose down -v
```

**Note:** Use `docker compose down -v` when you need to start completely fresh. This will wipe the PostgreSQL database and all volumes, so you'll need to rebuild containers and reload data from scratch.


## Common Commands

- `docker compose ps` - Check container status
- `docker compose logs -f` - View logs
- `docker compose logs app` - View app container logs
- `docker compose logs postgres` - View PostgreSQL logs
- `docker compose restart` - Restart all containers
- `docker compose exec app bash` - Open a bash shell in the app container
- `docker compose exec postgres psql -U admin -d data` - Connect to PostgreSQL via psql

## Troubleshooting

**Docker daemon not running:**
- Make sure Docker Desktop is running (check the menu bar/taskbar)
- Restart Docker Desktop if needed

**Port already in use:**
- Check if something is using port 8888: `lsof -i :8888`
- Or change the port in `docker-compose.yml`

**Container keeps restarting:**
- Check logs: `docker compose logs`
- Look for error messages