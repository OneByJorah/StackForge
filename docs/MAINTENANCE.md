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
tar czf honcho-backup.tgz /path/to/your/honcho/data
```
