# -*- coding: utf-8 -*-
"""
IELTS Master - 剑桥雅思官方机考与精听精读桌面客户端
"""

import os
import sys
import socket
import threading
import subprocess
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")

def get_server_port(start_port=18920):
    for p in range(start_port, start_port + 50):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', p))
                return p
        except OSError:
            continue
    return 18920

class SilentIELTSHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            pass

def start_server(port):
    server = ThreadingHTTPServer(('127.0.0.1', port), SilentIELTSHandler)
    server.serve_forever()

def launch_native_window(url):
    try:
        import webview
        window = webview.create_window(
            title="IELTS Master - 剑桥雅思官方机考与精听精读系统 (剑4 Test 1)",
            url=url,
            width=1440,
            height=920,
            min_size=(1024, 700),
            resizable=True,
            text_select=True,
            confirm_close=False
        )
        webview.start(debug=False)
        return True
    except Exception as e:
        print(f"[提示] 原生窗口拉起说明: {e}")
        return False

def launch_edge_app(url):
    try:
        cmd = f'start msedge --app="{url}" --window-size=1440,920'
        subprocess.Popen(cmd, shell=True)
        return True
    except Exception as e:
        print(f"[提示] 应用窗口唤起异常: {e}")
        return False

def main():
    port = get_server_port()
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    server_thread.start()

    url = f"http://127.0.0.1:{port}/index.html"
    print("=" * 60)
    print("  IELTS Master 雅思全真机考与精听系统已启动！")
    print(f"  本地服务地址: {url}")
    print("  正在为您打开独立客户端窗口...")
    print("=" * 60)

    if not launch_native_window(url):
        launch_edge_app(url)
        try:
            while True:
                server_thread.join(1)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()
