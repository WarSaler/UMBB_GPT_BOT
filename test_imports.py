#!/usr/bin/env python3
"""
Тестовый скрипт для диагностики проблем с импортом модулей
"""

import sys
import os

print("=== Python Environment Info ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
print(f"Current working directory: {os.getcwd()}")

print("\n=== Installed Packages ===")
try:
    import pkg_resources
    installed_packages = [d for d in pkg_resources.working_set]
    for package in sorted(installed_packages, key=lambda x: x.project_name.lower()):
        if 'telegram' in package.project_name.lower():
            print(f"Found: {package.project_name} {package.version}")
except ImportError:
    print("pkg_resources not available")

print("\n=== Testing Imports ===")

# Test 1: Try importing telegram
try:
    import telegram
    print("✅ Successfully imported 'telegram'")
    print(f"   telegram.__file__: {telegram.__file__}")
    print(f"   telegram.__version__: {getattr(telegram, '__version__', 'unknown')}")
except ImportError as e:
    print(f"❌ Failed to import 'telegram': {e}")

# Test 2: Try importing specific classes
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    print("✅ Successfully imported telegram classes")
except ImportError as e:
    print(f"❌ Failed to import telegram classes: {e}")

# Test 3: Try importing telegram.ext
try:
    from telegram.ext import Application, CommandHandler
    print("✅ Successfully imported telegram.ext")
except ImportError as e:
    print(f"❌ Failed to import telegram.ext: {e}")

# Test 4: Check if python-telegram-bot is installed
try:
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                          capture_output=True, text=True)
    if 'python-telegram-bot' in result.stdout:
        print("✅ python-telegram-bot found in pip list")
        for line in result.stdout.split('\n'):
            if 'python-telegram-bot' in line:
                print(f"   {line}")
    else:
        print("❌ python-telegram-bot not found in pip list")
except Exception as e:
    print(f"❌ Error checking pip list: {e}")

print("\n=== End of Diagnostics ===")