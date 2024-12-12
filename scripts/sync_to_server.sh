#!/bin/bash

# Create temporary directory for processing
TEMP_DIR=$(mktemp -d)
echo "Created temp directory: $TEMP_DIR"

# Copy current files to temp directory
cp -r /opt/person_of_interest/* $TEMP_DIR/

# Ensure correct directory structure
mkdir -p $TEMP_DIR/app/api
touch $TEMP_DIR/app/__init__.py
touch $TEMP_DIR/app/api/__init__.py
touch $TEMP_DIR/tests/__init__.py

# Move main.py to app directory if it exists in root
if [ -f "$TEMP_DIR/main.py" ]; then
    mv $TEMP_DIR/main.py $TEMP_DIR/app/main.py
fi

# Remove server prefix from imports in temp directory
find $TEMP_DIR -type f -name "*.py" -exec sed -i 's/from server\.app/from app/g' {} +
find $TEMP_DIR -type f -name "*.py" -exec sed -i 's/from server\./from /g' {} +

# Copy processed files back
rsync -av --exclude='.git/' --exclude='__pycache__/' \
    --exclude='*.prod.py' \
    $TEMP_DIR/ /opt/person_of_interest/

# Clean up
rm -rf $TEMP_DIR

# Set permissions
chmod -R 755 /opt/person_of_interest

# Install dependencies
echo "Installing dependencies..."

# Install other dependencies
conda install -y -c conda-forge \
    postgresql \
    asyncpg \
    sqlalchemy \
    pytest \
    pytest-asyncio \
    fastapi \
    uvicorn \
    python-dotenv \
    alembic \
    dlib \
    websockets \
    python-multipart \
    pydantic \
    pydantic-settings \
    pytest-cov \
    pytest-xdist \
    pytest-env \
    httpx \
    shapely

# Install ML packages with pip
pip install mediapipe==0.10.18
pip install pydantic-settings==2.1.0
pip install opencv-python==4.9.0.80
pip install numpy==1.26.4
pip install tensorflow-cpu==2.15.0
pip install ultralytics==8.1.27
pip install deep-sort-realtime==1.3.1

# Install PyJWT
pip install PyJWT==2.8.0

# Run tests
cd /opt/person_of_interest
PYTHONPATH=/opt/person_of_interest pytest tests -v