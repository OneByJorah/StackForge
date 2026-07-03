# J1-NOC Dashboard

Read-only monitoring dashboard for StackDeploy. Polls every service's real health
endpoint (the same ones in `docker-compose.yml` / `scripts/healthcheck.sh`) over the
internal Docker network, plus optional Portainer container stats.

**This does not replace or proxy anything.** Every service still exposes its own
port/API exactly as before — this just gives you one screen to see all of them at once.

## Install into StackDeploy

1. Drop this whole `noc-dashboard/` folder into the root of your `StackDeploy` repo,
   alongside `docker-compose.yml`.
2. Copy `docker-compose.dashboard.yml` to the repo root too (next to
   `docker-compose.honcho.yml` / `docker-compose.headroom.yml`).
3. (Optional) add to `.env`:
   ```
   PORTAINER_URL=http://<portainer-host>:9000
   PORTAINER_API_KEY=<your Portainer API key>
   NOC_POLL_INTERVAL=10
   ENABLE_HEADROOM_MONITORING=false
   ```
4. Deploy:
   ```
   docker compose -f docker-compose.yml -f docker-compose.dashboard.yml up -d --build
   ```
5. Open `http://<your-tailscale-ip>:9500`

## Running everything together

```
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dashboard.yml \
  -f docker-compose.portainer.yml \
  -f docker-compose.headroom.yml \
  up -d --build
```

Leave out `-f docker-compose.portainer.yml` or `-f docker-compose.headroom.yml` if you
don't want those. All overlays are independent — mix and match freely.

## Notes

- **Portainer is now a real service** (`docker-compose.portainer.yml`) — it was previously
  only mentioned in the README and healthcheck script with no actual compose definition.
  It's still optional/separate so you're not forced to run it. To wire the dashboard to it,
  set `PORTAINER_URL=http://portainer:9000` in `.env` (container-name resolution works
  automatically since both are on the same Docker network) and generate an API key in
  Portainer's UI for `PORTAINER_API_KEY`.
- **Fixed:** `headroom-qdrant` previously claimed host ports 6333/6334, colliding with the
  main `qdrant` service. It's remapped to 6335/6336 on the host in `docker-compose.headroom.yml`
  — internal container config is untouched, so nothing else needed to change.
- If you run the headroom overlay, set `ENABLE_HEADROOM_MONITORING=true` so the dashboard
  also monitors it.
- `honcho-db` and `honcho-redis` aren't published to the host in the main compose file,
  so the dashboard checks them over the internal Docker network only (TCP connect) —
  there's no "open service" link for those two by design.
- Adding a new service later: add one entry to the `SERVICES` list in `backend/app.py`
  with its container name, internal port, health path, and group — no frontend changes needed.
