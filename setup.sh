#!/bin/bash

# Alberta Land Use Feasibility Tool - Setup Script
echo "🏡 Setting up Alberta Land Use Feasibility Tool..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p reports
mkdir -p logs

# Run test to verify installation
echo "🧪 Running test to verify installation..."
python test_sample_property.py

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🌐 Then open your browser to: http://localhost:5000"
echo ""
echo "📋 To test with sample data:"
echo "   python test_sample_property.py"
