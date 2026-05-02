#!/bin/bash

echo "================================================"
echo "Signature Verification System - Installation"
echo "================================================"
echo ""

echo "Checking Python installation..."
python3 --version

if [ $? -ne 0 ]; then
    echo "ERROR: Python is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo ""
echo "Installing required libraries..."
echo "This may take a few minutes..."
echo ""

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to install some libraries"
    echo "Please check your internet connection and try again"
    exit 1
fi

echo ""
echo "================================================"
echo "Installation completed successfully!"
echo "================================================"
echo ""
echo "To start the system, run: ./run.sh"
echo ""
