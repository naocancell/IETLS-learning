# -*- coding: utf-8 -*-
"""
IELTS Master —— 剑桥雅思机考模拟 + 精听精读 本地客户端

启动：python ielts_client/app.py            （默认打开独立窗口）
      python ielts_client/app.py --browser  （用 Edge/默认浏览器打开）
      python ielts_client/app.py --server   （只启动本地服务，开发/调试用）

本地服务只监听 127.0.0.1，提供：
  /                 前端页面（web/）
  /data/...         题库 JSON 与图片（data/）
  /media/<key>      听力音频（自动从 听力/ 目录的 zip / mp3 中准备，支持 Range 拖动）
  /api/catalog      题库目录
  /api/store        学习记录（userdata/store.json，关窗不丢）
  /api/export       导出成绩 CSV 到 exports/
"""
import argparse
import json
import os
import re
import socket
import sys
import threading
import time
import traceback
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from media import MediaLibrary  # noqa: E402

APP_NAME = 'IELTS Master'
DEFAULT_CONFIG = {
    'port': 18920,
    'audio_dirs': ['听力'],
    'media_dir': 'ielts_client/media',
    'data_dir': 'ielts_client/data',
    'userdata_dir': 'userdata',
    'export_dir': 'exports',
    'window': {'width': 1440, 'height': 920},
}
MIME = {
    '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
    '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
    '.svg': 'image/svg+xml', '.webp': 'image/webp', '.ico': 'image/x-icon',
    '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.aac': 'audio/aac', '.wav': 'audio/wav',
    '.ogg': 'audio/ogg', '.flac': 'audio/flac', '.woff2': 'font/woff2', '.woff': 'font/woff',
    '.txt': 'text/plain; charset=utf-8', '.csv': 'text/csv; charset=utf-8',
}
MAX_BODY = 5 * 1024 * 1024


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    path = os.path.join(ROOT_DIR, 'config.json')
    if os.path.isfile(path):
        with open(path, encoding='utf-8-sig') as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    for k in ('media_dir', 'data_dir', 'userdata_dir', 'export_dir'):
        cfg[k] = os.path.join(ROOT_DIR, cfg[k])
    cfg['audio_dirs'] = [os.path.join(ROOT_DIR, d) for d in cfg['audio_dirs']]
    return cfg


class JsonStore:
    """线程安全、原子写入的简单键值存储。"""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.data = {}
        if os.path.isfile(path):
            try:
                with open(path, encoding='utf-8') as f:
                    self.data = json.load(f)
            except (OSError, ValueError):
                # 文件损坏时先备份，避免覆盖掉用户数据
                os.replace(path, path + '.broken-%d' % int(time.time()))
                self.data = {}

    def _flush(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def all(self):
        with self.lock:
            return json.dumps(self.data, ensure_ascii=False)

    def put(self, key, value):
        with self.lock:
            self.data[key] = value
            self._flush()

    def delete(self, key):
        with self.lock:
            if self.data.pop(key, None) is not None:
                self._flush()


class Catalog:
    def __init__(self, data_dir, media):
        self.data_dir = data_dir
        self.media = media

    def build(self):
        out = []
        if not os.path.isdir(self.data_dir):
            return out
        for book in sorted(os.listdir(self.data_dir)):
            bdir = os.path.join(self.data_dir, book)
            if not (os.path.isdir(bdir) and re.fullmatch(r'c\d{2}', book)):
                continue
            for test in sorted(os.listdir(bdir), key=_natural):
                tdir = os.path.join(bdir, test)
                if not os.path.isdir(tdir):
                    continue
                modules = {}
                label = None
                for module in ('listening', 'reading'):
                    fp = os.path.join(tdir, module + '.json')
                    if not os.path.isfile(fp):
                        continue
                    try:
                        with open(fp, encoding='utf-8') as f:
                            d = json.load(f)
                    except (OSError, ValueError) as e:
                        modules[module] = {'error': str(e)}
                        continue
                    base = '/data/%s/%s/' % (book, test)
                    info = {'path': base + module + '.json', 'base': base, 'title': d.get('title', ''),
                            'verified': bool(d.get('verified')), 'variant': d.get('variant')}
                    if module == 'listening':
                        missing = sorted({p['audio'] for p in d.get('parts', []) if p.get('audio') and not self.media.available(p['audio'])})
                        info['audio_ok'] = not missing
                        info['audio_missing'] = missing
                    modules[module] = info
                    if label is None and d.get('book'):
                        label = '剑%s Test %s' % (d['book'], d.get('test', test.lstrip('t')))
                if modules:
                    out.append({'id': '%s-%s' % (book, test), 'label': label or '%s %s' % (book, test), 'modules': modules})
        return out


def _natural(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'IELTSMaster/2'
        protocol_version = 'HTTP/1.1'

        def log_message(self, fmt, *args):  # 静默
            if app.verbose:
                sys.stderr.write('%s - %s\n' % (self.address_string(), fmt % args))

        # ---------- 工具 ----------
        def send_json(self, obj, status=200, raw=None):
            body = (raw if raw is not None else json.dumps(obj, ensure_ascii=False)).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def fail(self, status, msg=''):
            body = (msg or HTTPStatus(status).phrase).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)

        def read_body(self):
            n = int(self.headers.get('Content-Length') or 0)
            if n > MAX_BODY:
                raise ValueError('body too large')
            return self.rfile.read(n) if n else b''

        def same_origin(self):
            origin = self.headers.get('Origin')
            if not origin:
                return True
            return urlsplit(origin).hostname in ('127.0.0.1', 'localhost')

        def safe_join(self, root, rel):
            rel = rel.replace('\\', '/').lstrip('/')
            parts = [p for p in rel.split('/') if p not in ('', '.')]
            if any(p == '..' for p in parts):
                return None
            path = os.path.join(root, *parts)
            if not os.path.abspath(path).startswith(os.path.abspath(root)):
                return None
            return path

        def send_file(self, path, cache=False):
            if not path or not os.path.isfile(path):
                return self.fail(404)
            size = os.path.getsize(path)
            ctype = MIME.get(os.path.splitext(path)[1].lower(), 'application/octet-stream')
            start, end = 0, size - 1
            rng = self.headers.get('Range')
            status = 200
            if rng:
                m = re.fullmatch(r'bytes=(\d*)-(\d*)', rng.strip())
                if not m or (not m.group(1) and not m.group(2)):
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                if m.group(1):
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:  # bytes=-N
                    start = max(0, size - int(m.group(2)))
                end = min(end, size - 1)
                if start > end or start >= size:
                    self.send_response(416)
                    self.send_header('Content-Range', 'bytes */%d' % size)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                status = 206
            length = end - start + 1
            self.send_response(status)
            self.send_header('Content-Type', ctype)
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Content-Length', str(length))
            if status == 206:
                self.send_header('Content-Range', 'bytes %d-%d/%d' % (start, end, size))
            self.send_header('Cache-Control', 'max-age=86400' if cache else 'no-cache')
            self.end_headers()
            if self.command == 'HEAD':
                return
            try:
                with open(path, 'rb') as f:
                    f.seek(start)
                    left = length
                    while left > 0:
                        chunk = f.read(min(256 * 1024, left))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        left -= len(chunk)
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass

        # ---------- 路由 ----------
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            app.touch()
            path = unquote(urlsplit(self.path).path)
            try:
                if path in ('/', '/index.html'):
                    return self.send_file(os.path.join(app.web_dir, 'index.html'))
                if path == '/api/ping':
                    return self.send_json({'ok': True})
                if path == '/api/catalog':
                    return self.send_json(app.catalog.build())
                if path == '/api/store':
                    return self.send_json(None, raw=app.store.all())
                if path.startswith('/data/'):
                    return self.send_file(self.safe_join(app.cfg['data_dir'], path[len('/data/'):]))
                if path.startswith('/media/'):
                    key = path[len('/media/'):]
                    try:
                        real = app.media.ensure(key)
                    except Exception as e:  # 压缩包损坏等
                        return self.fail(500, '音频准备失败: %s' % e)
                    return self.send_file(real, cache=True)
                return self.send_file(self.safe_join(app.web_dir, path))
            except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
                pass

        def do_PUT(self):
            app.touch()
            path = unquote(urlsplit(self.path).path)
            if not self.same_origin():
                return self.fail(403)
            if path.startswith('/api/store/'):
                key = path[len('/api/store/'):]
                if not key or len(key) > 200:
                    return self.fail(400, 'bad key')
                try:
                    value = json.loads(self.read_body() or b'null')
                except ValueError:
                    return self.fail(400, 'bad json')
                app.store.put(key, value)
                return self.send_json({'ok': True})
            return self.fail(404)

        def do_DELETE(self):
            app.touch()
            path = unquote(urlsplit(self.path).path)
            if not self.same_origin():
                return self.fail(403)
            if path.startswith('/api/store/'):
                app.store.delete(path[len('/api/store/'):])
                return self.send_json({'ok': True})
            return self.fail(404)

        def do_POST(self):
            app.touch()
            path = unquote(urlsplit(self.path).path)
            if not self.same_origin():
                return self.fail(403)
            if path == '/api/export':
                try:
                    req = json.loads(self.read_body() or b'{}')
                except ValueError:
                    return self.fail(400, 'bad json')
                name = re.sub(r'[\\/:*?"<>|\r\n\t]+', '_', str(req.get('filename') or 'export.csv')).strip(' .') or 'export.csv'
                os.makedirs(app.cfg['export_dir'], exist_ok=True)
                out = os.path.join(app.cfg['export_dir'], name)
                # utf-8-sig：Excel 直接打开 CSV 不乱码
                with open(out, 'w', encoding='utf-8-sig', newline='') as f:
                    f.write(str(req.get('content') or ''))
                return self.send_json({'ok': True, 'path': out})
            return self.fail(404)

    return Handler


class App:
    def __init__(self, cfg, verbose=False):
        self.cfg = cfg
        self.verbose = verbose
        self.web_dir = os.path.join(BASE_DIR, 'web')
        self.media = MediaLibrary(cfg['audio_dirs'], cfg['media_dir'])
        self.catalog = Catalog(cfg['data_dir'], self.media)
        self.store = JsonStore(os.path.join(cfg['userdata_dir'], 'store.json'))
        self.last_seen = time.time()
        self.server = None

    def touch(self):
        self.last_seen = time.time()

    def start_server(self, port):
        self.server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(self))
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


def find_port(start):
    for p in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    raise RuntimeError('找不到可用端口（%d 起的 50 个端口都被占用）' % start)


def open_window(url, cfg):
    """优先用 pywebview 打开独立窗口；成功返回 True（窗口关闭后返回）。"""
    try:
        import webview
    except ImportError:
        log('未安装 pywebview（请先运行 setup.bat 或 pip install -r requirements.txt），改用浏览器打开。')
        return False
    w = cfg.get('window', {})
    webview.create_window(APP_NAME, url, width=w.get('width', 1440), height=w.get('height', 920),
                          min_size=(1024, 680), text_select=True)
    storage = os.path.join(cfg['userdata_dir'], 'webview')
    os.makedirs(storage, exist_ok=True)
    try:
        # private_mode=False：否则 pywebview 每次关闭都会清空 localStorage
        webview.start(private_mode=False, storage_path=storage)
    except TypeError:  # 旧版本 pywebview 没有这两个参数
        webview.start()
    return True


def open_browser(url):
    if os.name == 'nt':
        for exe in (r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe',
                    r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe',
                    r'%LocalAppData%\Microsoft\Edge\Application\msedge.exe'):
            exe = os.path.expandvars(exe)
            if os.path.isfile(exe):
                import subprocess
                subprocess.Popen([exe, '--app=' + url, '--window-size=1440,920'])
                return
    import webbrowser
    webbrowser.open(url)


def log(msg):
    if sys.stdout:
        try:
            print(msg, flush=True)
            return
        except Exception:
            pass


def fatal(msg):
    """pythonw / vbs 启动时没有控制台：写日志并弹窗提示。"""
    try:
        os.makedirs(os.path.join(ROOT_DIR, 'userdata'), exist_ok=True)
        with open(os.path.join(ROOT_DIR, 'userdata', 'app.log'), 'a', encoding='utf-8') as f:
            f.write(time.strftime('[%Y-%m-%d %H:%M:%S] ') + msg + '\n')
    except OSError:
        pass
    log(msg)
    if os.name == 'nt' and not sys.stdout:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg[:1500], APP_NAME + ' 启动失败', 0x10)
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description=APP_NAME)
    ap.add_argument('--port', type=int)
    ap.add_argument('--browser', action='store_true', help='不用独立窗口，直接用浏览器打开')
    ap.add_argument('--server', action='store_true', help='只启动本地服务（不打开窗口）')
    ap.add_argument('--verbose', action='store_true')
    args = ap.parse_args()

    cfg = load_config()
    app = App(cfg, verbose=args.verbose)
    port = find_port(args.port or int(cfg.get('port', 18920)))
    app.start_server(port)
    url = 'http://127.0.0.1:%d/' % port
    log('=' * 56)
    log('  %s 已启动：%s' % (APP_NAME, url))
    log('  已识别听力音频 %d 段；题库 %d 套' % (len(app.media.index), len(app.catalog.build())))
    if app.media.unmapped:
        log('  有 %d 个音频文件无法识别（见 python tools/prepare_media.py --check）' % len(app.media.unmapped))
    log('=' * 56)

    if args.server:
        _wait_forever()
        return
    if not args.browser and open_window(url, cfg):
        return  # 窗口已关闭
    open_browser(url)
    # 浏览器模式：页面每 20 秒发一次心跳，页面关闭 2 分钟后自动退出，避免后台残留进程
    log('  已在浏览器中打开；关闭页面约 2 分钟后服务自动退出（或按 Ctrl+C）。')
    try:
        while time.time() - app.last_seen < 120:
            time.sleep(5)
    except KeyboardInterrupt:
        pass


def _wait_forever():
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    try:
        main()
    except (SystemExit, KeyboardInterrupt):
        pass
    except BaseException:
        fatal(traceback.format_exc())
        sys.exit(1)
