# 233 runtime source baseline

On 2026-07-26, the active `anbo_wx` deployment contained uncommitted base-backend changes required by the NetOps integration. The changed tracked source files and the OA-username migration have been copied into this repository as the production baseline.

The NetOps-specific Flask route itself is intentionally owned by `NJCATV/netops-platform-api` under `platform-adapter/anbo_wx/`. This repository owns the host application, its normal mini-program/backend features, and migration dependencies.

Secrets, `.env` files, uploads, backup directories, logs, and database data are excluded.
