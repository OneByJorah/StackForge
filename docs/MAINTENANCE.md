# Maintenance

## Restart stack

```bash
docker compose restart
```

## Restart a single service

```bash
docker compose restart honcho-api
```

## View logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f searxng
docker compose logs -f honcho-api
docker compose logs -f ollama
```

## Update an image

```bash
docker compose pull searxng
docker compose up -d searxng
```

## Update all images

```bash
docker compose pull
docker compose up -d
```

## Backup Honcho memory

```bash
# Backup PostgreSQL data (Honcho memory)
docker compose exec honcho-db pg_dump -U honcho honcho > honcho-backup.sql

# Or backup the entire volume
tar czf honcho-backup.tgz /path/to/your/honcho/data
```

## Backup all volumes

```bash
docker compose down
tar czf stackforge-volumes-backup.tgz \
  /var/lib/docker/volumes/stackforge-*/_data
docker compose up -d
```

## Disk cleanup

```bash
# Remove unused Docker images
docker image prune -a

# Remove stopped containers
docker container prune
```