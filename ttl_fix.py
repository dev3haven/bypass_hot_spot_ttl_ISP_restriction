import sys
import subprocess
import importlib
import ipaddress
import argparse
from pathlib import Path

# ========== Auto-request administrator privileges (UAC) ==========
def run_as_admin():
    import ctypes
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True

    script = sys.argv[0]
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

# ========== Auto-install PyDivert ==========
def ensure_pydivert():
    """Ensure pydivert is installed."""
    try:
        import pydivert
        return pydivert
    except ImportError:
        print("[*] PyDivert not found. Installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "pydivert"],
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            pydivert = importlib.import_module('pydivert')
            print("[+] PyDivert installed successfully.")
            return pydivert
        except subprocess.CalledProcessError as e:
            print(f"[!] Installation error: {e}")
            print("[!] Try manually: pip install pydivert")
            input("Press Enter to exit...")
            sys.exit(1)

# ========== Traffic counter ==========
def increment_counter():
    """Increment shared traffic counter file."""
    try:
        counter_path = Path(__file__).parent / ".ttl_counter"
        count = 0
        if counter_path.exists():
            with open(counter_path, "r") as f:
                count = int(f.read().strip())
        count += 1
        with open(counter_path, "w") as f:
            f.write(str(count))
    except Exception:
        pass

# ========== Local networks ==========
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
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("ff00::/8"),
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

# ========== Main ==========
def main():
    parser = argparse.ArgumentParser(description="TTL Fix via WinDivert")
    parser.add_argument("--ipv4", dest="ipv4", action="store_true", default=True, help="Enable TTL change for IPv4")
    parser.add_argument("--no-ipv4", dest="ipv4", action="store_false", help="Disable TTL change for IPv4")
    parser.add_argument("--ipv6", dest="ipv6", action="store_true", default=True, help="Enable TTL change for IPv6")
    parser.add_argument("--no-ipv6", dest="ipv6", action="store_false", help="Disable TTL change for IPv6")
    parser.add_argument("--ipv4-ttl", type=int, default=65, help="Target TTL for IPv4")
    parser.add_argument("--ipv6-ttl", type=int, default=129, help="Target Hop Limit for IPv6")
    parser.add_argument("--skip-local", dest="skip_local", action="store_true", default=True, help="Do not change TTL for local IPs")
    parser.add_argument("--no-skip-local", dest="skip_local", action="store_false", help="Change TTL for local IPs too")
    args = parser.parse_args()

    if not args.ipv4 and not args.ipv6:
        print("[!] Neither IPv4 nor IPv6 selected. Nothing to do.")
        sys.exit(1)

    pydivert = ensure_pydivert()

    if args.ipv4 and args.ipv6:
        filter_str = "outbound"
    elif args.ipv4:
        filter_str = "outbound and ip"
    else:
        filter_str = "outbound and ipv6"

    print("[*] TTL Fix running.")
    if args.ipv4:
        print(f"    IPv4 TTL: {args.ipv4_ttl}")
    if args.ipv6:
        print(f"    IPv6 Hop Limit: {args.ipv6_ttl}")
    if args.skip_local:
        print("    Local traffic skipped.")
    print("[*] Press Ctrl+C to stop.")

    try:
        with pydivert.WinDivert(filter_str) as w:
            for packet in w:
                modified = False

                if args.ipv4 and packet.ipv4:
                    dst = packet.ipv4.dst_addr
                    if not (args.skip_local and is_local_ip(dst)):
                        packet.ipv4.ttl = args.ipv4_ttl
                        modified = True

                elif args.ipv6 and packet.ipv6:
                    dst = packet.ipv6.dst_addr
                    if not (args.skip_local and is_local_ip(dst)):
                        packet.ipv6.hop_limit = args.ipv6_ttl
                        modified = True

                if modified:
                    packet.recalculate_checksums()
                    increment_counter()

                w.send(packet)

    except KeyboardInterrupt:
        print("\n[*] Stopped.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    run_as_admin()
    main()
