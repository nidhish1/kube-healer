#!/bin/bash
# Quick activation script for the virtual environment

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: make venv"
    exit 1
fi

echo "✅ Activating virtual environment..."
source venv/bin/activate

echo "🐍 Python: $(python --version)"
echo "📦 Pip: $(pip --version)"
echo ""
echo "Virtual environment activated!"
echo "Run 'deactivate' to exit the virtual environment"
