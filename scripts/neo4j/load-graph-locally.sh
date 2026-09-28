#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: $0 <path to neo4j.dump>" >&2
  exit 1
fi

DUMP_FILE=$1
NEO4J_IMAGE=neo4j:2026.01.4-community-trixie
CONTAINER_NAME=plantgenie-neo4j
NEO4J_PASSWORD=${NEO4J_PASSWORD:-plantgenie}
DATA_DIRECTORY=${DATA_DIRECTORY:-$HOME/plantgenie-neo4j/data}

if [ ! -f "$DUMP_FILE" ]; then
  echo "no such file: $DUMP_FILE" >&2
  exit 1
fi

STAGING_DIRECTORY=$(mktemp -d)
trap 'rm -rf "$STAGING_DIRECTORY"' EXIT
cp "$DUMP_FILE" "$STAGING_DIRECTORY/neo4j.dump"

mkdir -p "$DATA_DIRECTORY"
DATA_DIRECTORY=$(cd "$DATA_DIRECTORY" && pwd)

docker rm --force "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "loading $DUMP_FILE into $DATA_DIRECTORY"
docker run --rm \
  --volume "$DATA_DIRECTORY":/data \
  --volume "$STAGING_DIRECTORY":/backup \
  "$NEO4J_IMAGE" \
  neo4j-admin database load neo4j --from-path=/backup --overwrite-destination=true

echo "starting $CONTAINER_NAME"
docker run --detach \
  --name "$CONTAINER_NAME" \
  --publish 7474:7474 \
  --publish 7687:7687 \
  --volume "$DATA_DIRECTORY":/data \
  --env NEO4J_AUTH="neo4j/$NEO4J_PASSWORD" \
  "$NEO4J_IMAGE" >/dev/null

echo
echo "neo4j is starting up, it takes about a minute the first time"
echo "browser:  http://localhost:7474"
echo "bolt:     bolt://localhost:7687"
echo "user:     neo4j"
echo "password: $NEO4J_PASSWORD"
echo
echo "stop it with:   docker stop $CONTAINER_NAME"
echo "start it again: docker start $CONTAINER_NAME"
