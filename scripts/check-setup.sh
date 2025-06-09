#!/bin/bash

echo "Poromet Setup Checker"
echo "===================="

# Check Python
echo "Checking Python..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python not found"
    exit 1
fi

# Check Python packages
echo "Checking Python packages..."
REQUIRED_PACKAGES="porespy fastapi uvicorn numpy matplotlib scikit-image pillow python-multipart"

for package in $REQUIRED_PACKAGES; do
    python -c "import ${package//-/_}" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $package"
    else
        echo "❌ $package (run: pip install $package)"
    fi
done

# Check Node.js
echo ""
echo "Checking Node.js..."
node --version
if [ $? -ne 0 ]; then
    echo "❌ Node.js not found"
    exit 1
fi

# Check if we can start the backend
echo ""
echo "Testing backend startup..."
cd api
timeout 10s python analyze.py &
BACKEND_PID=$!
sleep 3

curl -s http://127.0.0.1:5328/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backend can start successfully"
else
    echo "❌ Backend failed to start"
fi

kill $BACKEND_PID 2>/dev/null
cd ..

echo ""
echo "Setup check complete!"
echo "To start the application, run: bash scripts/start-dev.sh"
