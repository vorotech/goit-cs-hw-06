# goit-cs-hw-06

## Getting Started

### Running with Docker Compose

To start the application and MongoDB:

```bash
docker compose up -d
```

To view logs:
```bash
docker compose logs -f
```

To stop the application:
```bash
docker compose down
```

To force rebuild containers:
```bash
docker compose build --no-cache  # rebuild without using cache
docker compose up -d --force-recreate  # start with fresh containers
```

To clean up everything (including volumes):
```bash
docker compose down -v --rmi all  # removes containers, networks, volumes, and images
```

## Development

### Start MongoDB for Development

Launch only MongoDB service with Docker Compose:

```bash
docker compose up mongodb -d
```

Verify MongoDB is running:
```bash
docker compose ps
```

### Activate Virtual Environment

Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run Application

With MongoDB running in Docker, start the application:

```bash
python src/server/main.py
```

The application will connect to MongoDB using these default parameters.
