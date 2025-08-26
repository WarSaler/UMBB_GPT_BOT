#!/usr/bin/env python3
import urllib.request
import json

def check_bot_status():
    try:
        # Check main page
        print("=== Checking main page ===")
        response = urllib.request.urlopen('https://umbb-gpt-bot.onrender.com/')
        html = response.read().decode()
        print(f"Status: {response.status}")
        print(f"Content length: {len(html)}")
        print("First 500 characters:")
        print(html[:500])
        print("\n" + "="*50 + "\n")
        
        # Check health endpoint
        print("=== Checking health endpoint ===")
        try:
            response = urllib.request.urlopen('https://umbb-gpt-bot.onrender.com/health')
            health_data = response.read().decode()
            print(f"Status: {response.status}")
            print(f"Health response: {health_data}")
        except Exception as e:
            print(f"Health endpoint error: {e}")
            
    except Exception as e:
        print(f"Error checking bot: {e}")

if __name__ == "__main__":
    check_bot_status()