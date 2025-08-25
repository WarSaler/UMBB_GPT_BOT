#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная диагностика модулей и зависимостей для Telegram Bot
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def check_python_info():
    print_separator("PYTHON INFORMATION")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

def check_installed_packages():
    print_separator("INSTALLED PACKAGES")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting package list: {e}")
        print(f"stderr: {e.stderr}")

def check_telegram_modules():
    print_separator("TELEGRAM MODULE DIAGNOSTICS")
    
    # Проверяем различные способы импорта telegram
    modules_to_check = [
        'telegram',
        'telegram.ext',
        'telegram.constants',
        'python_telegram_bot',
    ]
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ {module_name}: OK")
            print(f"   Location: {getattr(module, '__file__', 'Built-in')}")
            if hasattr(module, '__version__'):
                print(f"   Version: {module.__version__}")
        except ImportError as e:
            print(f"❌ {module_name}: FAILED - {e}")
        except Exception as e:
            print(f"⚠️  {module_name}: ERROR - {e}")

def check_specific_imports():
    print_separator("SPECIFIC IMPORTS CHECK")
    
    imports_to_check = [
        ('telegram', 'Update'),
        ('telegram', 'InlineKeyboardButton'),
        ('telegram', 'InlineKeyboardMarkup'),
        ('telegram.ext', 'Application'),
        ('telegram.ext', 'CommandHandler'),
        ('telegram.ext', 'MessageHandler'),
        ('telegram.ext', 'CallbackQueryHandler'),
        ('telegram.ext', 'filters'),
        ('telegram.ext', 'ContextTypes'),
        ('telegram.constants', 'ParseMode'),
    ]
    
    for module_name, item_name in imports_to_check:
        try:
            module = importlib.import_module(module_name)
            item = getattr(module, item_name)
            print(f"✅ from {module_name} import {item_name}: OK")
        except ImportError as e:
            print(f"❌ from {module_name} import {item_name}: IMPORT ERROR - {e}")
        except AttributeError as e:
            print(f"❌ from {module_name} import {item_name}: ATTRIBUTE ERROR - {e}")
        except Exception as e:
            print(f"⚠️  from {module_name} import {item_name}: ERROR - {e}")

def check_other_dependencies():
    print_separator("OTHER DEPENDENCIES CHECK")
    
    dependencies = [
        'openai',
        'PIL',
        'pytesseract',
        'requests',
        'Flask',
        'loguru',
    ]
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            print(f"✅ {dep}: OK")
            if hasattr(module, '__version__'):
                print(f"   Version: {module.__version__}")
        except ImportError as e:
            print(f"❌ {dep}: FAILED - {e}")
        except Exception as e:
            print(f"⚠️  {dep}: ERROR - {e}")

def check_file_structure():
    print_separator("PROJECT FILE STRUCTURE")
    
    current_dir = Path('.')
    files_to_check = [
        'bot.py',
        'openai_handler.py',
        'ocr_handler.py',
        'translator.py',
        'requirements.txt',
        'render.yaml',
        'runtime.txt',
    ]
    
    for file_name in files_to_check:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name}: EXISTS ({file_path.stat().st_size} bytes)")
        else:
            print(f"❌ {file_name}: NOT FOUND")

def check_environment_variables():
    print_separator("ENVIRONMENT VARIABLES")
    
    env_vars = [
        'TELEGRAM_BOT_TOKEN',
        'OPENAI_API_KEY',
        'OPENAI_MODEL',
        'PYTHON_VERSION',
        'PORT',
    ]
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Скрываем секретные токены
            if 'TOKEN' in var or 'KEY' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")

def main():
    print("🔍 ПОЛНАЯ ДИАГНОСТИКА TELEGRAM BOT")
    print(f"Время запуска: {__import__('datetime').datetime.now()}")
    
    try:
        check_python_info()
        check_installed_packages()
        check_telegram_modules()
        check_specific_imports()
        check_other_dependencies()
        check_file_structure()
        check_environment_variables()
        
        print_separator("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("✅ Диагностика успешно выполнена!")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА ДИАГНОСТИКИ: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()