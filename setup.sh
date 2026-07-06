#!/usr/bin/env bash
# FederalSpendAI VPS installer — CyberPanel / bare Linux (Ubuntu, AlmaLinux, Rocky).
# Binds MCP to localhost by default so OpenLiteSpeed (80/443) stays untouched.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/SBPnet/federal-spend-ai.git}"
REPO_BRANCH="${REPO_BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/federalspendai}"
CONTAINER_NAME="${CONTAINER_NAME:-federalspendai}"
IMAGE_NAME="${IMAGE_NAME:-federalspendai}"
VOLUME_NAME="${VOLUME_NAME:-federalspendai-data}"
BIND_HOST="${BIND_HOST:-127.0.0.1}"
BIND_PORT="${BIND_PORT:-8000}"
DATA_SOURCE="${DATA_SOURCE:-live}"
WITH_SWAP="${WITH_SWAP:-0}"
SKIP_DOCKER_INSTALL="${SKIP_DOCKER_INSTALL:-0}"
SKIP_INIT="${SKIP_INIT:-0}"

usage() {
  cat <<'EOF'
FederalSpendAI VPS setup (CyberPanel-friendly)

Installs Docker if needed, builds the image, runs an initial analysis cycle, and
starts the FederalSpendAI engine (auto-pull + analyze + MCP plugin host) on
localhost so OpenLiteSpeed / website ports (80/443) are not affected.

Usage:
  ./setup.sh [options]

Options:
  --install-dir PATH     Install location (default: /opt/federalspendai)
  --branch NAME          Git branch to deploy (default: main)
  --data SOURCE          fixtures | live | skip (default: live)
  --bind HOST:PORT       Listen address (default: 127.0.0.1:8000)
  --with-swap            Create a 2G swapfile if none exists
  --skip-docker-install  Assume Docker is already installed (e.g. CyberPanel Docker)
  --skip-init            Skip initial cycle (engine still auto-pulls on start)
  -h, --help             Show this help

Examples:
  sudo ./setup.sh
  sudo ./setup.sh --data live --with-swap
  sudo BIND_HOST=0.0.0.0 ./setup.sh --data skip   # public MCP (use firewall + auth)

After setup, connect from your laptop:
  ssh -L 8000:127.0.0.1:8000 root@YOUR_VPS_IP

Docs: https://github.com/SBPnet/federal-spend-ai
EOF
}

log() { printf '==> %s\n' "$*"; }
die() { printf 'Error: %s\n' "$*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --branch) REPO_BRANCH="$2"; shift 2 ;;
    --data) DATA_SOURCE="$2"; shift 2 ;;
    --bind)
      BIND_HOST="${2%%:*}"
      BIND_PORT="${2##*:}"
      shift 2
      ;;
    --with-swap) WITH_SWAP=1; shift ;;
    --skip-docker-install) SKIP_DOCKER_INSTALL=1; shift ;;
    --skip-init) SKIP_INIT=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1 (try --help)" ;;
  esac
done

case "$DATA_SOURCE" in
  fixtures|live|skip) ;;
  *) die "--data must be fixtures, live, or skip" ;;
esac

if [[ "$(id -u)" -ne 0 ]]; then
  die "Run as root (e.g. sudo ./setup.sh). CyberPanel VPS SSH is usually root@IP."
fi

detect_os() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_VERSION="${VERSION_ID:-}"
  else
    die "Cannot detect OS (/etc/os-release missing)."
  fi
}

docker_ready() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

install_docker_debian() {
  log "Installing Docker (Debian/Ubuntu)..."
  apt-get update -qq
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL "https://download.docker.com/linux/${OS_ID}/gpg" -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${OS_ID} ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
}

install_docker_rhel() {
  log "Installing Docker (RHEL family)..."
  dnf -y install dnf-plugins-core
  dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
}

ensure_docker() {
  if docker_ready; then
    log "Docker is already available."
    return
  fi
  if [[ "$SKIP_DOCKER_INSTALL" == "1" ]]; then
    die "Docker not available and --skip-docker-install was set."
  fi
  detect_os
  case "$OS_ID" in
    ubuntu|debian) install_docker_debian ;;
    almalinux|rocky|centos|rhel|cloudlinux) install_docker_rhel ;;
    *) die "Unsupported OS for auto Docker install: ${OS_ID}. Install Docker manually or use CyberPanel Docker Manager." ;;
  esac
  docker_ready || die "Docker failed to start."
}

ensure_swap() {
  if [[ "$WITH_SWAP" != "1" ]]; then
    return
  fi
  if swapon --show | grep -q .; then
    log "Swap already enabled."
    return
  fi
  log "Creating 2G swapfile..."
  fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
}

clone_or_update() {
  if [[ -f "${INSTALL_DIR}/Dockerfile" ]]; then
    log "Updating existing install at ${INSTALL_DIR}..."
    git -C "$INSTALL_DIR" fetch origin "$REPO_BRANCH"
    git -C "$INSTALL_DIR" checkout "$REPO_BRANCH"
    git -C "$INSTALL_DIR" pull --ff-only origin "$REPO_BRANCH"
  else
    log "Cloning ${REPO_URL} (branch ${REPO_BRANCH}) to ${INSTALL_DIR}..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --branch "$REPO_BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR"
  fi
}

build_image() {
  log "Building Docker image ${IMAGE_NAME}..."
  docker build -t "$IMAGE_NAME" "$INSTALL_DIR"
}

stop_existing_container() {
  if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    log "Removing existing container ${CONTAINER_NAME}..."
    docker rm -f "$CONTAINER_NAME" >/dev/null
  fi
}

run_init() {
  if [[ "$SKIP_INIT" == "1" || "$DATA_SOURCE" == "skip" ]]; then
    log "Skipping initial engine cycle."
    return
  fi

  case "$DATA_SOURCE" in
    fixtures)
      log "Loading sample fixtures, then running one engine cycle..."
      docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        -v "${INSTALL_DIR}/tests/fixtures:/fixtures:ro" \
        -e FEDERALSPEND_DATA_DIR=/data \
        "$IMAGE_NAME" \
        sh -c "federalspendai ingest --datasets awards,public_accounts --fixture-dir /fixtures && federalspendai engine --once"
      ;;
    live)
      log "Running initial live ingest/analyze cycle (network required)..."
      docker run --rm \
        -v "${VOLUME_NAME}:/data" \
        -e FEDERALSPEND_DATA_DIR=/data \
        -e FEDERALSPEND_ENGINE_DATASETS=awards,public_accounts \
        "$IMAGE_NAME" \
        federalspendai engine --once
      ;;
  esac
}

start_server() {
  log "Starting FederalSpendAI engine on ${BIND_HOST}:${BIND_PORT}..."
  stop_existing_container
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    -p "${BIND_HOST}:${BIND_PORT}:8000" \
    -v "${VOLUME_NAME}:/data" \
    -e FEDERALSPEND_DATA_DIR=/data \
    -e FEDERALSPEND_ENGINE_ENABLED=true \
    -e FEDERALSPEND_ENGINE_DATASETS=awards,public_accounts \
    -e FEDERALSPEND_ENGINE_POLL_INTERVAL_SECONDS=3600 \
    -e FEDERALSPEND_ENGINE_RUN_ON_START=true \
    "$IMAGE_NAME" \
    federalspendai engine --transport sse --port 8000

  log "Engine status:"
  docker run --rm -v "${VOLUME_NAME}:/data" -e FEDERALSPEND_DATA_DIR=/data "$IMAGE_NAME" federalspendai status
}

print_summary() {
  cat <<EOF

FederalSpendAI engine is running.

  Container:  ${CONTAINER_NAME}
  Engine MCP: http://${BIND_HOST}:${BIND_PORT}
  Data vol:   ${VOLUME_NAME}
  Install:    ${INSTALL_DIR}
  Plugins:    /data/plugins.json (auto-created)

The engine auto-pulls open Canada data, refreshes embeddings, and detects
anomalies every hour (configurable via FEDERALSPEND_ENGINE_POLL_INTERVAL_SECONDS).

CyberPanel / OpenLiteSpeed: websites on 80/443 are unchanged.
Default bind is localhost only — use an SSH tunnel for remote access:

  ssh -L ${BIND_PORT}:127.0.0.1:${BIND_PORT} root@YOUR_VPS_IP

Logs:    docker logs -f ${CONTAINER_NAME}
Restart: docker restart ${CONTAINER_NAME}
Status:  docker run --rm -v ${VOLUME_NAME}:/data ${IMAGE_NAME} federalspendai status

Re-run one analysis cycle manually:
  docker run --rm -v ${VOLUME_NAME}:/data ${IMAGE_NAME} federalspendai engine --once

Add MCP plugins in /var/lib/docker/volumes/${VOLUME_NAME}/_data/plugins.json
(or mount a custom plugins.json into /data/plugins.json).

EOF
}

main() {
  log "FederalSpendAI VPS setup"
  detect_os
  log "Detected OS: ${OS_ID} ${OS_VERSION:-}"
  ensure_swap
  ensure_docker
  if ! command -v git >/dev/null 2>&1; then
    case "$OS_ID" in
      ubuntu|debian) apt-get update -qq && apt-get install -y git ;;
      almalinux|rocky|centos|rhel|cloudlinux) dnf -y install git ;;
    esac
  fi
  clone_or_update
  build_image
  run_init
  start_server
  print_summary
}

main "$@"
