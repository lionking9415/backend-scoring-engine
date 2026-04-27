#!/bin/bash
# Build script for frontend with nvm

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

nvm use 20
GENERATE_SOURCEMAP=false npm run build
