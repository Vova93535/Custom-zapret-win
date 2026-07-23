#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для извлечения IP-адресов из файла list_general.txt (домены и IP)
и добавления уникальных IP в ipset_all.txt.
Пути к файлам заданы абсолютные: C:\zapret-discord-youtube\lists\
"""

import socket
import sys
from ipaddress import ip_address

# Конфигурация
INPUT_FILE = r"C:\\zapret-discord-youtube\\lists\\list-general.txt"
OUTPUT_FILE = r"C:\\zapret-discord-youtube\\lists\\ipset-all.txt"
DNS_TIMEOUT = 5  # секунды

# Устанавливаем глобальный таймаут для всех сетевых операций (включая DNS)
socket.setdefaulttimeout(DNS_TIMEOUT)

def is_ip(address: str) -> bool:
    """Проверяет, является ли строка IPv4 или IPv6 адресом."""
    try:
        ip_address(address.strip())
        return True
    except ValueError:
        return False

def resolve_domain(domain: str) -> set:
    """
    Возвращает множество IP-адресов (IPv4 и IPv6) для заданного домена.
    При ошибках DNS возвращает пустое множество.
    """
    ips = set()
    domain = domain.strip().lower()
    if not domain:
        return ips

    try:
        # getaddrinfo без параметра timeout, но общий таймаут уже установлен через setdefaulttimeout
        addrinfo = socket.getaddrinfo(domain, None)
        for _, _, _, _, sockaddr in addrinfo:
            ip = sockaddr[0]
            if is_ip(ip):
                ips.add(ip)
    except socket.gaierror:
        print(f"⚠️ Не удалось разрешить домен: {domain}", file=sys.stderr)
    except socket.timeout:
        print(f"⏱️ Таймаут DNS при разрешении: {domain}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Ошибка при разрешении {domain}: {e}", file=sys.stderr)
    return ips

def load_existing_ips(file_path: str) -> set:
    """Загружает уже имеющиеся IP-адреса из файла ipset_all.txt."""
    existing = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and is_ip(line):
                    existing.add(line)
    except FileNotFoundError:
        print(f"ℹ️ Файл {file_path} не найден, будет создан новый.", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ Ошибка при чтении {file_path}: {e}", file=sys.stderr)
    return existing

def save_ips(file_path: str, ips: set):
    """Сохраняет множество IP-адресов в файл (каждый с новой строки)."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for ip in sorted(ips, key=lambda x: (isinstance(ip_address(x), type(ip_address('0.0.0.0'))), x)):
                f.write(ip + '\n')
        print(f"✅ Сохранено {len(ips)} уникальных IP в {file_path}")
    except Exception as e:
        print(f"❌ Ошибка при записи в {file_path}: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # 1. Загружаем существующие IP из выходного файла
    all_ips = load_existing_ips(OUTPUT_FILE)
    original_count = len(all_ips)
    print(f"📁 Найдено {original_count} IP в {OUTPUT_FILE}")

    # 2. Читаем входной файл построчно
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ Файл не найден: {INPUT_FILE}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при чтении {INPUT_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    new_ips = set()
    for raw_line in lines:
        line = raw_line.strip()
        # Пропускаем пустые строки и комментарии (начинающиеся с # или ;)
        if not line or line.startswith('#') or line.startswith(';'):
            continue

        if is_ip(line):
            new_ips.add(line)
        else:
            domain_ips = resolve_domain(line)
            if domain_ips:
                print(f"🌐 {line} -> {', '.join(domain_ips)}")
                new_ips.update(domain_ips)
            else:
                print(f"⚠️ Не удалось получить IP для: {line}", file=sys.stderr)

    # 3. Добавляем найденные IP к уже существующим
    added_ips = new_ips - all_ips
    all_ips.update(new_ips)

    # 4. Сохраняем результат (перезаписываем файл)
    if added_ips:
        print(f"✨ Добавлено {len(added_ips)} новых IP:")
        for ip in sorted(added_ips):
            print(f"   + {ip}")
    else:
        print("ℹ️ Новых IP не обнаружено.")

    save_ips(OUTPUT_FILE, all_ips)

if __name__ == "__main__":
    main()