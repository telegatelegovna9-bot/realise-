#!/usr/bin/env bash
set -e

# Установка системных зависимостей для компиляции
apt-get update -qq && apt-get install -y build-essential wget

# Скачивание и установка TA-Lib C-библиотеки
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib
./configure --prefix=/usr
make
make install

# Указываем компилятору, где искать заголовки и библиотеки TA-Lib
export CFLAGS="-I/usr/include/ta-lib" LDFLAGS="-L/usr/lib"

# Установка Python-зависимостей
pip install -r requirements.txt

# Очистка временных файлов
rm -rf /tmp/ta-lib*