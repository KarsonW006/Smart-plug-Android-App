# Smart Home System (A-level Project)

This repository contains Python modules for a smart-home system, including device control, scheduling, usage retrieval, data synchronisation, and data processing.

## Important setup notes

- This portfolio copy has had database credentials, email addresses, device PINs, internal hostnames, and local deployment paths replaced with placeholders.
- The original online database/backend is not configured in this public copy. Features that depend on it will not work until you configure your own authorised environment.
- Do not commit real passwords, API keys, tokens, device PINs, private keys, database dumps, or personal data.
- Configure credentials using environment variables or a local, untracked configuration file rather than hardcoding them in source code.
- Runtime database and log files are excluded by `.gitignore`.

## Project modules

- `updater/` — device and system update tasks
- `tapo/` — Tapo smart-device controls
- `getUsages/` — energy usage retrieval
- `yeelight/` — Yeelight device controls
- `scheduler/` — scheduled jobs
- `dataSync/` — data synchronisation and notifications
- `dataMart/` — data processing and database access

## Before running

Review each module's dependencies and configure valid credentials and endpoints in a secure local environment. Do not put real secrets in this public repository.
