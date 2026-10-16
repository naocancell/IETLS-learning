/*
 * IELTS Master - 本地持久化
 * 首选写入本地 Python 服务（ielts_client/userdata/store.json），
 * 因为 pywebview 默认使用隐私模式，关闭窗口后 localStorage 会被清空。
 * 服务不可用时退回 localStorage。
 */
(function (global) {
  'use strict';
  const LS_PREFIX = 'ielts.v2.';
  const timers = {};
  const Store = {
    data: {},
    server: false,
    async init() {
      try {
        const res = await fetch('/api/store', { cache: 'no-store' });
        if (!res.ok) throw new Error(res.status);
        this.data = await res.json();
        this.server = true;
      } catch (e) {
        this.server = false;
        this.data = {};
        try {
          for (let i = 0; i < localStorage.length; i++) {
            const k = localStorage.key(i);
            if (k.startsWith(LS_PREFIX)) this.data[k.slice(LS_PREFIX.length)] = JSON.parse(localStorage.getItem(k));
          }
        } catch (_) { /* ignore */ }
      }
    },
    get(key, def) {
      return Object.prototype.hasOwnProperty.call(this.data, key) ? this.data[key] : def;
    },
    set(key, value, immediate) {
      this.data[key] = value;
      try { localStorage.setItem(LS_PREFIX + key, JSON.stringify(value)); } catch (_) { /* ignore */ }
      if (!this.server) return;
      clearTimeout(timers[key]);
      const send = () => fetch('/api/store/' + encodeURIComponent(key), {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(value === undefined ? null : value)
      }).catch(() => {});
      if (immediate) send(); else timers[key] = setTimeout(send, 400);
    },
    remove(key) {
      delete this.data[key];
      try { localStorage.removeItem(LS_PREFIX + key); } catch (_) { /* ignore */ }
      if (this.server) fetch('/api/store/' + encodeURIComponent(key), { method: 'DELETE' }).catch(() => {});
    }
  };
  global.Store = Store;
})(window);
