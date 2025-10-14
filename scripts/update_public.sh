#!/bin/bash

cd frontend

echo "🔄 Syncing source files to public folder..."

# Create necessary directories
mkdir -p public/ui

# Sync package.json
echo "📦 Copying package.json..."
cp package.json public/

# Sync AppContext
echo " Copying AppContext.tsx..."
cp src/context/AppContext.tsx public/

# Create components listing with glob
echo "📋 Creating components listing..."
find src/components/ui -name "*.tsx" -o -name "*.ts" | sed 's|src/components/ui/||' | sed 's/\.tsx$//' | sed 's/\.ts$//' > public/ui-components.txt

echo "✅ Files synced successfully!"

cd -
