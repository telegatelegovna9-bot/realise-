#!/usr/bin/env bash
set -e

# Журналирование для отладки
echo "Starting TA-Lib installation process..."

# Установка системных зависимостей
echo "Installing system dependencies..."
apt-get update -qq && apt-get install -y build-essential wget || { echo "Failed to install system dependencies"; exit 1; }

# Обновление pip
echo "Upgrading pip..."
pip install --upgrade pip || { echo "Failed to upgrade pip"; exit 1; }

# Установка TA-Lib C-библиотеки
echo "Downloading TA-Lib..."
cd /tmp
wget --retry-connrefused --waitretry=1 --timeout=20 http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz || { echo "Failed to download TA-Lib"; exit 1; }
echo "Extracting TA-Lib..."
tar -xzf ta-lib-0.4.0-src.tar.gz || { echo "Failed to extract TA-Lib"; exit 1; }
cd ta-lib
echo "Configuring TA-Lib..."
./configure --prefix=/usr || { echo "Configure failed"; exit 1; }
echo "Building TA-Lib..."
make || { echo "Make failed"; exit 1; }
echo "Installing TA-Lib..."
make install || { echo "Make install failed"; exit 1; }

# Проверка установки TA-Lib
echo "Checking for TA-Lib headers..."
if [ -f /usr/include/ta-lib/ta_defs.h ]; then
    echo "TA-Lib headers found at /usr/include/ta-lib/ta_defs.h"
else
    echo "ERROR: TA-Lib headers NOT found at /usr/include/ta-lib/ta_defs.h"
    exit 1
fi

# Установка путей для компилятора
echo "Setting CFLAGS and LDFLAGS..."
export CFLAGS="-I/usr/include/ta-lib -I/usr/local/include/ta-lib"
export LDFLAGS="-L/usr/lib -L/usr/local/lib"

# Установка Python-зависимостей
echo "Installing Python dependencies..."
pip install -r requirements.txt || { echo "Failed to install Python dependencies"; exit 1; }

# Очистка
echo "Cleaning up..."
rm -rf /tmp/ta-lib*
