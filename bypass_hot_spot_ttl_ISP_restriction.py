import sys
import subprocess
import importlib
import ipaddress

# ========== Авто-запрос прав администратора (UAC) ==========
def run_as_admin():
    import ctypes
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True

    script = sys.argv[0]
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

# ========== Автоустановка PyDivert ==========
def ensure_pydivert():
    try:
        import pydivert
        return pydivert
    except ImportError:
        print("[*] PyDivert не найден. Устанавливаем...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pydivert"],
                stdout=sys.stdout, stderr=sys.stderr
            )
            pydivert = importlib.import_module('pydivert')
            print("[+] PyDivert успешно установлен.")
            return pydivert
        except subprocess.CalledProcessError as e:
            print(f"[!] Ошибка установки: {e}")
            print("[!] Попробуйте вручную: pip install pydivert")
            input("Нажмите Enter для выхода...")
            sys.exit(1)

# ========== Локальные сети ==========
LOCAL_NETWORKS_V4 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
]

LOCAL_NETWORKS_V6 = [
    ipaddress.ip_network("::1/128"),          # loopback
    ipaddress.ip_network("fe80::/10"),        # link-local
    ipaddress.ip_network("fc00::/7"),          # unique local
    ipaddress.ip_network("ff00::/8"),          # multicast
]

def is_local_ip(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.version == 4:
            return any(ip in network for network in LOCAL_NETWORKS_V4)
        else:
            return any(ip in network for network in LOCAL_NETWORKS_V6)
    except ValueError:
        return True

# ========== Основной код ==========
def main():
    pydivert = ensure_pydivert()

    print("[*] TTL Fix активен.")
    print("[*] IPv4 внешний: TTL = 65")
    print("[*] IPv6 внешний: Hop Limit = 129")
    print("[*] Локальный трафик (IPv4 + IPv6) пропускается без изменений.")
    print("[*] Нажмите Ctrl+C для остановки.\n")
    
    try:
        # outbound — ловит и IPv4, и IPv6
        with pydivert.WinDivert("outbound") as w:
            for packet in w:
                modified = False
                
                if packet.ipv4:
                    dst = packet.ipv4.dst_addr
                    if not is_local_ip(dst):
                        packet.ipv4.ttl = 65
                        modified = True
                
                elif packet.ipv6:
                    dst = packet.ipv6.dst_addr
                    if not is_local_ip(dst):
                        packet.ipv6.hop_limit = 129
                        modified = True
                
                if modified:
                    packet.recalculate_checksums()
                
                w.send(packet)
                
    except KeyboardInterrupt:
        print(f"\n[*] Остановлено.")
    except Exception as e:
        print(f"\n[!] Ошибка: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    run_as_admin()
    main()
