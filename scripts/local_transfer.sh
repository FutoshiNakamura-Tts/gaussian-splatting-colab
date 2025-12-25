#!/bin/bash

# Configuration
# HOST should match the entry in your ~/.ssh/config for the Colab instance
HOST="colab"
REMOTE_USER="root"
REMOTE_HOST="${REMOTE_USER}@${HOST}"

# Defaults
REMOTE_BASE="/content/gaussian-splatting"
REMOTE_DATA="/content/data"
REMOTE_OUTPUT="${REMOTE_BASE}/output"

usage() {
    echo "Usage: $0 [command] [options]"
    echo "Commands:"
    echo "  upload <path>    : Upload file/folder to Colab (/content/data)"
    echo "  download <name>  : Download specific experiment folder from Colab output"
    echo "  sync-latest      : Download the most recent experiment output"
    echo "  list             : List experiments in Colab output folder"
    exit 1
}

ensure_remote_dirs() {
    ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DATA $REMOTE_OUTPUT"
}

cmd_upload() {
    SRC="$1"
    if [ -z "$SRC" ]; then echo "Error: Missing source path."; usage; fi
    
    echo "=== Uploading $SRC to $REMOTE_HOST:$REMOTE_DATA ==="
    ensure_remote_dirs
    # -a: archive mode, -h: human readable, -v: verbose, -z: compress, -P: progress/partial
    if [ -d "$SRC" ]; then
        # If directory, ensure we upload INTO target
        rsync -ahvzP "$SRC" "$REMOTE_HOST:$REMOTE_DATA/"
    else
        rsync -ahvzP "$SRC" "$REMOTE_HOST:$REMOTE_DATA/"
    fi
}

cmd_list() {
    echo "=== Remote Experiments in $REMOTE_OUTPUT ==="
    ssh "$REMOTE_HOST" "ls -F $REMOTE_OUTPUT"
}

cmd_download() {
    NAME="$1"
    if [ -z "$NAME" ]; then echo "Error: Missing experiment name."; usage; fi
    
    echo "=== Downloading $NAME from Colab ==="
    # Download to current directory's 'downloads' folder or just current dir?
    # Let's verify remote exists
    if ssh "$REMOTE_HOST" "[ -e $REMOTE_OUTPUT/$NAME ]"; then
        rsync -ahvzP "$REMOTE_HOST:$REMOTE_OUTPUT/$NAME" ./
    else
        echo "Error: Remote path $REMOTE_OUTPUT/$NAME does not exist."
    fi
}

cmd_sync_latest() {
    echo "=== Finding latest experiment... ==="
    # Find directory with latest mtime in output
    # Ignoring zip files, looking for directories usually
    LATEST=$(ssh "$REMOTE_HOST" "ls -td $REMOTE_OUTPUT/*/ | head -1")
    
    if [ -z "$LATEST" ]; then
        echo "No output directories found."
        exit 1
    fi
    
    # Strip trailing slash and get basename
    LATEST_NAME=$(basename "${LATEST%/}")
    echo "Latest experiment: $LATEST_NAME"
    
    cmd_download "$LATEST_NAME"
}

case "$1" in
    upload)
        cmd_upload "$2"
        ;;
    download)
        cmd_download "$2"
        ;;
    sync-latest)
        cmd_sync_latest
        ;;
    list)
        cmd_list
        ;;
    *)
        usage
        ;;
esac
