#!/bin/sh
# couchdb-init.sh — CouchDB first-boot setup
# Creates sync user, enables CORS.
# Runs inside the livesync-init container (curlimages/curl)
set -e

echo "⟳ CouchDB init — configuring CORS + sync user..."

AUTH="${COUCHDB_ADMIN_USER:?}:${COUCHDB_ADMIN_PASSWORD:?}"
BASE="http://${AUTH}@127.0.0.1:5984"

# Detect CouchDB node name (varies in Docker)
NODE=$(curl -sf "${BASE}/_membership" | sed 's/.*"all_nodes":\["\([^"]*\)"\].*/\1/')
[ -z "$NODE" ] && NODE="nonode@nohost"
echo "  Node: ${NODE}"

# Create sync user
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/admins/${COUCHDB_SYNC_USER}" \
  -H "Content-Type: application/json" \
  -d "\"${COUCHDB_SYNC_PASSWORD}\"" || true

# Enable CORS
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/httpd/enable_cors"    -d '"true"' || true
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/cors/origins"         -d '"*"' || true
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/cors/credentials"     -d '"true"' || true
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/cors/methods"         -d '"GET, PUT, POST, HEAD, DELETE"' || true
curl -sf -X PUT "${BASE}/_node/${NODE}/_config/cors/headers"         -d '"accept, authorization, content-type, origin, referer, x-couchdb-request"' || true

echo "✓ CouchDB ready — admin:${COUCHDB_ADMIN_USER}  sync:${COUCHDB_SYNC_USER}  CORS=*"