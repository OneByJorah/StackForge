---
title: "Welcome"
date: 2026-07-04 19:00:00
tags: [system,guide]
---

# Welcome to Your AI Brain

This shared vault is the **persistent memory layer** for your Hermes fleet.

## How it works

- **Agents** write session summaries here automatically
- **Syncthing** syncs these notes to your laptop's Obsidian
- **CouchDB LiveSync** provides real-time sync (alternative)
- **Web viewer** at `http://<server-ip>:8083` for quick reading

## Directory

```
obsidian/vault/
├── YYYY-MM-DD-topic-slug.md   ← agent-generated notes
├── Welcome.md                  ← this file
└── index.json                  ← auto-generated for the web viewer
```

## Tips

- Add your own `.md` files — they appear in the sidebar
- Tag notes with `[agent, status]` for easy filtering
- The web viewer auto-regenerates its index every 5 minutes