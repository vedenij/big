# Big Node - Delegation Server Setup

This is a **Big Node** configuration that provides GPU computation services for small nodes during PoC benchmark phase.

## Key Differences from Small Node

- **NO blockchain services** (no tmkms, node, api, explorer, proxy)
- **ONLY delegation server** for GPU computation
- Does NOT participate in consensus
- Does NOT sign batches (small nodes sign with their own keys)
- Only used during 5-minute PoC benchmark at epoch start

## Prerequisites

1. NVIDIA GPU server (50-200+ GPUs recommended)
2. Docker with NVIDIA runtime
3. Git with submodules initialized

## Setup Instructions

### 1. Clone and Initialize

```bash
cd /path/to/big
git submodule update --init --recursive
```

### 2. Configure Environment

```bash
cd deploy/join
cp config.env.template config.env
nano config.env
```

Set the following variables:
- `HF_HOME`: Path to shared ML model cache (e.g., `/mnt/shared`)
- `DELEGATION_PORT`: Port for delegation API (default: 9090)
- `DELEGATION_MAX_SESSIONS`: Max concurrent delegation sessions (default: 10)
- `DELEGATION_AUTH_TOKEN`: Secret token for authentication (CHANGE THIS!)

### 3. Deploy

#### Option A: Local Development (recommended)

Build image from local files without pushing to GitHub:

```bash
cd deploy/join
./deploy-local.sh
```

After making code changes, quickly rebuild:

```bash
./rebuild.sh
```

#### Option B: Production Deployment

Use pre-built image from GitHub registry:

```bash
# Load configuration
source config.env

# Pull images
docker compose -f docker-compose.yml -f docker-compose.mlnode.yml pull

# Start services
docker compose -f docker-compose.yml -f docker-compose.mlnode.yml up -d

# Check logs
docker logs -f mlnode-308
```

### 4. Verify

```bash
# Check health
curl http://localhost:9090/health

# Check delegation API (requires auth token)
curl -H "Authorization: Bearer your-secret-token" \
  http://localhost:9090/api/v1/delegation/sessions
```

## Architecture

```
┌─────────────────────────────────────┐
│          mlnode-308                 │
│  (ghcr.io/vedenij/bigmlnode:3.0.11)│
│         Port: 9090                  │
│                                     │
│  - DelegationServer                 │
│  - API: /api/v1/delegation/*        │
│  - Auto GPU detection               │
│  - Session management               │
│  - Batch generation                 │
│                                     │
│  GPUs: ALL (NVIDIA)                 │
└─────────────────────────────────────┘
```

## Delegation API Endpoints

- `POST /api/v1/delegation/start` - Start new delegation session
- `GET /api/v1/delegation/batch/{session_id}` - Get next batch
- `GET /api/v1/delegation/sessions` - List active sessions
- `DELETE /api/v1/delegation/session/{session_id}` - Stop session

## Security

1. **ALWAYS change** `DELEGATION_AUTH_TOKEN` from default
2. Use firewall to restrict access to port 9090
3. Only allow connections from trusted small nodes
4. Consider using VPN or private network

## Troubleshooting

### GPU not detected
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of memory
- Reduce `DELEGATION_MAX_SESSIONS` in config.env
- Check GPU memory: `nvidia-smi`

### Authentication errors
- Verify `DELEGATION_AUTH_TOKEN` matches on both big and small nodes
- Check Authorization header format: `Bearer <token>`

## Monitoring

```bash
# View logs
docker logs -f mlnode-308

# Check active sessions
curl -H "Authorization: Bearer your-secret-token" \
  http://localhost:9090/api/v1/delegation/sessions

# GPU usage
nvidia-smi -l 1
```
