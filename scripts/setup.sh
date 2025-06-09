#!/bin/bash

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Node.js dependencies (handled by Next.js)
echo "Installing Node.js dependencies..."
npm install

echo "Setup complete!"
echo ""
echo "To run the application:"
echo "1. Start the FastAPI backend: python api/analyze.py"
echo "2. Start the Next.js frontend: npm run dev"
echo "3. Open http://localhost:3000 in your browser"
