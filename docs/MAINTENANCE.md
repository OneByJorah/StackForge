# Maintenance

## Restart stack

```bash
docker compose restart
```

## Update model

```bash
docker compose up -d llama-server
```

## Backup Honcho memory

```bash
tar czf honcho-backup.tgz /home/j1admin/docker/j1-stack-deploy/honcho
```
