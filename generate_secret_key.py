#!/usr/bin/env python3
"""
Скрипт для генерации Django Secret Key
"""

from django.core.management.utils import get_random_secret_key

if __name__ == "__main__":
    secret_key = get_random_secret_key()
    print("Django Secret Key:")
    print(secret_key)
    print("\nДобавьте эту строку в ваш .env файл:")
    print(f"DJANGO_SECRET_KEY={secret_key}")
