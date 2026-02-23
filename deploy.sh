#!/bin/bash

# Deploy script for NBA Player Similarity to RMI NAS (Synology)
# Git-based deployment: pull on NAS from GitHub, rebuild Docker containers

set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
SSH_HOST="nas"  # SSH config host entry (~/.ssh/config)
REMOTE_DIR="/volume1/docker/nba-player-similarity"
DOCKER="/usr/local/bin/docker"
DEPLOY_BRANCH="main"

# Auto-install gum if missing (https://github.com/charmbracelet/gum)
if ! command -v gum &>/dev/null; then
    echo "gum not found — installing via brew..."
    brew install gum
fi

# Flags
DRY_RUN=false
SKIP_BUILD=false
DO_INGEST=false

# ============================================================================
# USAGE & LOGGING
# ============================================================================

usage() {
    cat << 'EOF'

  NBA Player Similarity — NAS Deploy Script

  USAGE
    ./deploy.sh [OPTIONS]

  OPTIONS
    -h, --help          Show this help message
    -n, --dry-run       Show what would happen without making changes
    -b, --branch NAME   Deploy a specific branch (default: main)
    --skip-build        Pull code only, skip Docker rebuild
    --ingest            Re-ingest data after deploy (needed when vector size changes)

  EXAMPLES
    ./deploy.sh                          Deploy main branch (pull + rebuild)
    ./deploy.sh -b feature/new-ui        Deploy a feature branch
    ./deploy.sh --ingest                 Deploy and re-ingest all player data
    ./deploy.sh --skip-build             Pull latest code, don't rebuild containers
    ./deploy.sh -n                       Dry run — preview without changes
  WORKFLOW
    1. Commit and push your changes to GitHub
    2. Run ./deploy.sh (or ./deploy.sh --ingest if embeddings changed)
    3. Script pulls on NAS, rebuilds containers, verifies health

  FIRST TIME SETUP
    1. Install Git Server package on Synology NAS
    2. Add "Host nas" entry to ~/.ssh/config (HostName + User)
    3. SSH into NAS: git clone https://github.com/ValmeI/nba-player-similarity.git /volume1/docker/nba-player-similarity
    4. Set up passwordless sudo for Docker on NAS (see README)
    5. Run: ./deploy.sh --ingest         (first deploy with data ingestion)

EOF
    exit 0
}

_ts() { date '+%Y-%m-%d %H:%M:%S'; }
log()         { echo "$(_ts)  $*"; }
log_success() { gum style --foreground 2 "$(_ts) $*"; }
log_error()   { gum style --foreground 1 "$(_ts) $*" 1>&2; }
log_warning() { gum style --foreground 3 "$(_ts) $*"; }
log_section() { echo ""; gum style --foreground 8 "── $* ──"; }

# ============================================================================
# REMOTE EXECUTION
# ============================================================================

remote() {
    local cmd="$1"
    local msg="${2:-}"

    if [[ "$DRY_RUN" == true ]]; then
        [[ -n "$msg" ]] && log "$msg"
        echo "[DRY RUN] Would execute: $cmd"
        return 0
    fi

    if [[ -n "$msg" ]]; then
        gum spin --spinner dot --show-output --title "$msg" -- \
            ssh "${SSH_HOST}" "$cmd"
    else
        ssh "${SSH_HOST}" "$cmd"
    fi
}

remote_sudo() {
    local cmd="$1"
    local msg="${2:-}"

    if [[ "$DRY_RUN" == true ]]; then
        [[ -n "$msg" ]] && log "$msg"
        echo "[DRY RUN] Would execute (sudo): sudo $cmd"
        return 0
    fi

    if [[ -n "$msg" ]]; then
        gum spin --spinner dot --show-output --title "$msg" -- \
            ssh "${SSH_HOST}" "sudo $cmd"
    else
        ssh "${SSH_HOST}" "sudo $cmd"
    fi
}


# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

preflight() {
    log_section "Pre-flight Checks"

    # SSH connectivity
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "${SSH_HOST}" "echo ok" > /dev/null 2>&1; then
        log_error "Cannot SSH to ${SSH_HOST}"
        exit 1
    fi
    log_success "SSH connectivity OK"

    # Git repo on NAS
    if ! remote "cd $REMOTE_DIR && git rev-parse --git-dir" > /dev/null 2>&1; then
        log_error "No git repo at $REMOTE_DIR on NAS"
        log "Run: ssh ${SSH_HOST} 'cd /volume1/docker && git clone https://github.com/ValmeI/nba-player-similarity.git'"
        exit 1
    fi
    log_success "Git repository OK"

    # Docker available
    if ! remote "sudo $DOCKER info" > /dev/null 2>&1; then
        log_error "Docker not accessible — ensure passwordless sudo is configured for docker"
        exit 1
    fi
    log_success "Docker OK"

    # Check disk space
    if [[ "$DRY_RUN" == false ]]; then
        local free_kb
        free_kb=$(remote "df -k $REMOTE_DIR | tail -1 | awk '{print \$4}'")
        if [[ $free_kb -lt 1048576 ]]; then
            log_warning "Low disk space: $(( free_kb / 1024 )) MB free"
        else
            log_success "Disk space OK: $(( free_kb / 1024 )) MB free"
        fi
    fi

    log_success "All pre-flight checks passed"
}

# ============================================================================
# ENV FILE SYNC
# ============================================================================

sync_env_docker() {
    log_section "Sync .env_docker"

    # Always copy .env_docker to NAS so new vars are never missed
    local env_source=".env_docker"
    if [[ ! -f "$env_source" ]]; then
        env_source=".env_EXAMPLE"
    fi
    ssh "${SSH_HOST}" "cat > ${REMOTE_DIR}/.env_docker" < "$env_source"
    log_success "Copied .env_docker to NAS"

    # Inject real LLM_API_KEY from local .env
    if remote "grep -q 'xxxxxxxxxxxxxxxxxxxxx' $REMOTE_DIR/.env_docker" > /dev/null 2>&1; then
        if [[ -f ".env" ]]; then
            local api_key
            api_key=$(grep '^LLM_API_KEY' .env | sed 's/.*=\s*"\?\([^"]*\)"\?/\1/')
            if [[ -n "$api_key" && "$api_key" != "xxxxxxxxxxxxxxxxxxxxx" ]]; then
                remote "sed -i 's|xxxxxxxxxxxxxxxxxxxxx|${api_key}|' $REMOTE_DIR/.env_docker"
                log_success "LLM_API_KEY injected from local .env"
            else
                log_warning "No real API key in local .env — set LLM_API_KEY on NAS manually"
            fi
        else
            log_warning "No local .env file — set LLM_API_KEY on NAS manually"
        fi
    else
        log_success "LLM_API_KEY already set"
    fi
}

# ============================================================================
# GIT OPERATIONS
# ============================================================================

check_local() {
    log_section "Local Check"

    # Warn if local has unpushed commits
    local ahead
    ahead=$(git rev-list --count "origin/$DEPLOY_BRANCH..HEAD" 2>/dev/null || echo "0")
    if [[ "$ahead" -gt 0 ]]; then
        log_warning "You have $ahead unpushed commit(s) on $DEPLOY_BRANCH — push first if you want them deployed"
    else
        log_success "Local is in sync with origin/$DEPLOY_BRANCH"
    fi
}

pull_on_nas() {
    log_section "Pull on NAS"

    local current_commit
    current_commit=$(remote "cd $REMOTE_DIR && git rev-parse --short HEAD")
    log "Current NAS commit: $current_commit"

    # Checkout correct branch
    remote "cd $REMOTE_DIR && git fetch origin" "Fetching from GitHub..."
    remote "cd $REMOTE_DIR && git checkout $DEPLOY_BRANCH 2>/dev/null || git checkout -b $DEPLOY_BRANCH origin/$DEPLOY_BRANCH" \
        "Checking out $DEPLOY_BRANCH..."
    remote "cd $REMOTE_DIR && git pull origin $DEPLOY_BRANCH" "Pulling latest..."

    local new_commit
    new_commit=$(remote "cd $REMOTE_DIR && git rev-parse --short HEAD")
    if [[ "$current_commit" == "$new_commit" ]]; then
        log_success "Already up to date ($new_commit)"
    else
        log_success "Updated: $current_commit -> $new_commit"
    fi
}

# ============================================================================
# DOCKER OPERATIONS
# ============================================================================

docker_rebuild() {
    log_section "Docker Rebuild"

    remote_sudo "cd $REMOTE_DIR && $DOCKER compose down" "Stopping containers..."
    remote_sudo "cd $REMOTE_DIR && $DOCKER compose up --build -d" "Building and starting containers..."

    # Wait for containers to stabilize
    sleep 5

    log_success "Docker containers rebuilt"
}

data_ingest() {
    log_section "Data Ingestion"

    local container
    container=$(remote "sudo $DOCKER ps -qf 'name=nba-app'" | tr -d '[:space:]')

    if [[ -z "$container" ]]; then
        log_error "nba-app container not running — cannot ingest"
        return 1
    fi

    log "This may take a few minutes..."
    remote_sudo "$DOCKER exec $container python -m tasks.data_ingesting.ingest_data_main" \
        "Ingesting data into Qdrant (27D vectors)..."

    log_success "Data ingestion complete"
}

# ============================================================================
# VERIFICATION
# ============================================================================

verify() {
    log_section "Verification"

    # Check containers
    local containers
    containers=$(remote "sudo $DOCKER compose -f $REMOTE_DIR/docker-compose.yml ps --format '{{.Name}} {{.Status}}'" 2>/dev/null || \
                 remote "sudo $DOCKER ps --filter 'name=nba-player' --format '{{.Names}} {{.Status}}'")

    if echo "$containers" | grep -qi "nba-app.*up\|nba-app.*running"; then
        log_success "nba-app container is running"
    else
        log_error "nba-app container is NOT running"
    fi

    if echo "$containers" | grep -qi "streamlit.*up\|streamlit.*running"; then
        log_success "streamlit-app container is running"
    else
        log_error "streamlit-app container is NOT running"
    fi

    if echo "$containers" | grep -qi "qdrant.*up\|qdrant.*running"; then
        log_success "qdrant container is running"
    else
        log_error "qdrant container is NOT running"
    fi

    # Check Streamlit is responding
    if remote "curl -s -o /dev/null -w '%{http_code}' http://localhost:8501" 2>/dev/null | grep -q "200"; then
        log_success "Streamlit UI responding at :8501"
    else
        log_warning "Streamlit UI not responding yet (may still be starting)"
    fi

    # Check FastAPI is responding
    if remote "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs" 2>/dev/null | grep -q "200"; then
        log_success "FastAPI responding at :8000"
    else
        log_warning "FastAPI not responding yet (may still be starting)"
    fi

    # Show NAS commit
    local commit
    commit=$(remote "cd $REMOTE_DIR && git log -1 --oneline")
    log "Deployed commit: $commit"
}

# ============================================================================
# CLI ARGUMENT PARSING
# ============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)       usage ;;
        -n|--dry-run)    DRY_RUN=true; log_warning "DRY RUN MODE"; shift ;;
        -b|--branch)     DEPLOY_BRANCH="$2"; shift 2 ;;
        --skip-build)    SKIP_BUILD=true; shift ;;
        --ingest)        DO_INGEST=true; shift ;;
        *)               log_error "Unknown option: $1"; usage ;;
    esac
done

# ============================================================================
# MAIN
# ============================================================================

main() {
    gum style \
        --border-foreground 8 \
        --border normal --align center \
        --width 50 --padding "1 4" \
        "NBA Player Similarity Deploy" "" \
        "Target: ${SSH_HOST}" \
        "Branch: ${DEPLOY_BRANCH}"

    preflight
    check_local
    pull_on_nas
    sync_env_docker

    if [[ "$SKIP_BUILD" == false ]]; then
        docker_rebuild
    else
        log_warning "Skipping Docker rebuild (--skip-build)"
    fi

    if [[ "$DO_INGEST" == true ]]; then
        data_ingest
    fi

    verify

    echo ""
    log_success "Deployment complete!"
    echo ""
    local nas_ip
    nas_ip=$(ssh -G "$SSH_HOST" | awk '/^hostname / {print $2}')
    log "Streamlit UI: http://${nas_ip}:8501"
    log "FastAPI docs: http://${nas_ip}:8000/docs"
}

main
