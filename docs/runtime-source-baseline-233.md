# 233 runtime source baseline

On 2026-07-26, the historical pre-cutover deployment contained uncommitted base-backend changes required by the NetOps integration. The changed tracked source files and the OA-username migration have been copied into this repository as the production baseline. The active source path after cutover is `/srv/netops/netops-littleProgram`.

The NetOps-specific Flask route itself is intentionally owned by `NJCATV/netops-platform-api` under `platform-adapter/host-application/`. This repository owns the host application, its normal mini-program/backend features, and migration dependencies.

Secrets, `.env` files, uploads, backup directories, logs, and database data are excluded.
