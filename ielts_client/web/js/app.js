/* IELTS Master - 主控制器：套题加载、模考/练习流程、音频、计时、成绩与历史 */
(function () {
  'use strict';
  const S = window.IELTSScoring, R = window.IELTSRender, Store = window.Store;
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const esc = R.esc;

  const CATEGORY = {
    note_completion: '笔记填空', table_completion: '表格填空', sentence_completion: '句子填空',
    summary_completion: '摘要填空', form_completion: '表单填空', flow_chart: '流程图填空',
    plan_labelling: '地图/平面图', diagram_labelling: '示意图标注', chart_labelling: '图表配对',
    diagram_matching: '图形配对', multiple_choice: '单选题', multi_choice: '多选题',
    matching: '配对题', matching_headings: '段落标题配对', matching_information: '段落信息配对',
    matching_features: '特征配对', matching_sentence_endings: '句尾配对',
    tfng: '判断题 T/F/NG', ynng: '判断题 Y/N/NG', short_answer: '简答题'
  };
  const CHOICE_TYPES = ['single_choice', 'tfng', 'ynng', 'matching', 'multi_choice'];
  const READING_SECONDS = 60 * 60;
  const LISTENING_REVIEW_SECONDS = 2 * 60; // 机考听力结束后的检查时间

  const state = {
    catalog: [], entry: null, testId: null, module: 'listening', mode: 'study',
    data: null, base: '', index: {}, order: [],
    answers: {}, flags: new Set(), partIdx: 0, focusQ: null,
    phase: 'practice', remaining: 0, elapsed: 0, paused: false, tick: null,
    mockPart: 0, durations: [], transcripts: {}, ab: null, showTranscript: false,
    passageCache: {}, lastReport: null
  };
  const audio = $('#audio');

  // ---------------------------------------------------------------- 工具
  const fmt = (sec) => {
    sec = Math.max(0, Math.floor(sec || 0));
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
    return (h ? h + ':' + String(m).padStart(2, '0') : String(m).padStart(2, '0')) + ':' + String(s).padStart(2, '0');
  };
  async function getJSON(url) {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(url + ' → HTTP ' + r.status);
    return r.json();
  }
  let toastTimer = null;
  function toast(msg, ms) {
    const t = $('#toast');
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, ms || 2600);
  }
  const parts = () => (state.data ? state.data.parts : []);
  const part = () => parts()[state.partIdx];
  const progKey = () => `progress:${state.testId}:${state.module}:${state.mode}`;
  const mockKey = () => `mock:${state.testId}:${state.module}`;

  function saveProgress() {
    Store.set(progKey(), { answers: state.answers, flags: Array.from(state.flags), updated: Date.now() });
  }
  function savePrefs() {
    const p = Store.get('prefs', {});
    Object.assign(p, { testId: state.testId, module: state.module, mode: state.mode });
    Store.set('prefs', p);
  }

  // ---------------------------------------------------------------- 启动
  async function init() {
    await Store.init();
    // 心跳：浏览器模式下服务据此判断页面是否已关闭
    setInterval(() => { fetch('/api/ping', { cache: 'no-store' }).catch(() => {}); }, 20000);
    const prefs = Store.get('prefs', {});
    setFont(prefs.font || 'm');
    try {
      state.catalog = await getJSON('/api/catalog');
    } catch (e) {
      $('#pane-b').innerHTML = `<div class="empty">无法读取题库目录（${esc(e.message)}）。<br>请通过 <code>run.bat</code> / <code>python ielts_client/app.py</code> 启动，不要直接双击 index.html。</div>`;
      return;
    }
    const sel = $('#test-select');
    sel.innerHTML = state.catalog.map(t => {
      const flags = Object.values(t.modules).some(m => !m.verified) ? ' · 未核对' : '';
      return `<option value="${esc(t.id)}">${esc(t.label)}${flags}</option>`;
    }).join('');
    if (!state.catalog.length) {
      $('#pane-b').innerHTML = '<div class="empty">题库为空。请参考 docs/修复记录与剑5-21导入指南.md 添加套题。</div>';
      return;
    }
    state.testId = state.catalog.some(t => t.id === prefs.testId) ? prefs.testId : state.catalog[0].id;
    state.module = prefs.module === 'reading' ? 'reading' : 'listening';
    state.mode = prefs.mode === 'mock' ? 'mock' : 'study';
    bindEvents();
    await load();
  }

  async function load() {
    stopTick(); stopAudio();
    state.entry = state.catalog.find(t => t.id === state.testId);
    if (!state.entry.modules[state.module]) state.module = Object.keys(state.entry.modules)[0];
    const meta = state.entry.modules[state.module];
    $('#test-select').value = state.testId;
    try {
      state.data = await getJSON(meta.path);
    } catch (e) {
      $('#pane-b').innerHTML = `<div class="empty">题库文件读取失败：${esc(e.message)}</div>`;
      return;
    }
    state.base = meta.base;
    state.partIdx = 0; state.passageCache = {}; state.transcripts = {}; state.ab = null; state.focusQ = null;
    buildIndex();
    const prog = Store.get(progKey(), null) || { answers: {}, flags: [] };
    state.answers = prog.answers || {}; state.flags = new Set(prog.flags || []);
    document.body.classList.toggle('mod-listening', state.module === 'listening');
    document.body.classList.toggle('mod-reading', state.module === 'reading');
    document.body.classList.toggle('mode-mock', state.mode === 'mock');
    document.body.classList.toggle('mode-study', state.mode === 'study');
    $$('#module-seg button').forEach(b => {
      b.classList.toggle('active', b.dataset.module === state.module);
      b.disabled = !state.entry.modules[b.dataset.module];
    });
    $$('#mode-seg button').forEach(b => b.classList.toggle('active', b.dataset.mode === state.mode));
    savePrefs();
    if (state.mode === 'mock') prepareMock(); else startPractice();
  }

  function buildIndex() {
    state.index = {}; state.order = [];
    parts().forEach((p, pi) => p.groups.forEach(g => g.questions.forEach(q => {
      state.index[q.id] = { q, g, pi };
      state.order.push(q.id);
    })));
    state.order.sort((a, b) => a - b);
  }

  // ---------------------------------------------------------------- 渲染
  function renderAll() {
    renderPaneA();
    renderQuestions();
    renderNav();
    renderPlayerbar();
  }

  function renderPaneA() {
    const pane = $('#pane-a');
    if (state.module === 'reading') {
      const p = part();
      if (state.passageCache[state.partIdx]) { pane.innerHTML = state.passageCache[state.partIdx]; return; }
      pane.innerHTML = `
        <div class="passage">
          <div class="passage-kicker">${esc(p.title)}</div>
          ${p.intro ? `<div class="passage-intro">${R.inline(p.intro)}</div>` : ''}
          ${p.show_title !== false && p.passage_title ? `<h2 class="passage-title">${esc(p.passage_title)}</h2>` : ''}
          <div class="passage-body">${R.markup(p.passage, { imgBase: state.base })}</div>
        </div>`;
      pane.scrollTop = 0;
      return;
    }
    // 听力：练习模式下显示原文面板
    const show = state.mode === 'study' && state.showTranscript;
    document.body.classList.toggle('with-transcript', show);
    if (!show) { pane.innerHTML = ''; return; }
    const p = part();
    const tr = state.transcripts[state.partIdx];
    if (!p.transcript) { pane.innerHTML = '<div class="empty small">本段暂无录音原文。</div>'; return; }
    if (!tr) {
      pane.innerHTML = '<div class="empty small">正在加载原文…</div>';
      getJSON(state.base + p.transcript).then(d => { state.transcripts[state.partIdx] = d; renderPaneA(); })
        .catch(() => { pane.innerHTML = '<div class="empty small">原文文件读取失败。</div>'; });
      return;
    }
    const note = tr.source === 'asr'
      ? `<div class="tr-note">⚠️ 本原文由语音识别自动生成（${esc(tr.model || 'whisper')}），可能有个别错词，仅供精听参考；以官方 Tapescript 为准。</div>` : '';
    pane.innerHTML = `<div class="transcript"><div class="tr-head"><b>${esc(p.title)} · 录音原文</b><span class="muted">点击句子跳转播放</span></div>${note}
      <div class="tr-list">${(tr.segments || []).map((s, i) => `<div class="tr-seg" data-i="${i}" data-start="${s.start}"><span class="ts">${fmt(s.start)}</span><span>${esc(s.text)}</span></div>`).join('')}</div></div>`;
  }

  function renderQuestions() {
    const p = part();
    const pane = $('#pane-b');
    const [a, b] = p.questions_range || [p.groups[0].range[0], p.groups[p.groups.length - 1].range[1]];
    const disabled = state.mode === 'mock' && state.phase !== 'running' && state.phase !== 'review';
    let h = `<div class="part-head"><b>${esc(state.module === 'listening' ? 'Part ' + p.number : p.title)}</b><span>Questions ${a}–${b}</span>${state.data.verified ? '' : '<span class="badge warn">题库未核对</span>'}</div>`;
    h += p.groups.map(g => R.renderGroup(g, { answers: state.answers, imgBase: state.base, study: state.mode === 'study', disabled })).join('');
    pane.innerHTML = h;
    pane.scrollTop = 0;
    markFlags();
  }

  function renderNav() {
    const wrap = $('#nav-parts');
    wrap.innerHTML = parts().map((p, pi) => {
      const ids = state.order.filter(id => state.index[id].pi === pi);
      const done = ids.filter(isAnswered).length;
      const nums = ids.map(id => `<button class="nq${isAnswered(id) ? ' done' : ''}${state.flags.has(id) ? ' flag' : ''}${state.focusQ === id ? ' cur' : ''}" data-q="${id}">${id}</button>`).join('');
      const label = state.module === 'listening' ? 'Part ' + p.number : 'Passage ' + p.number;
      return `<div class="nav-part${pi === state.partIdx ? ' active' : ''}" data-part="${pi}">
        <button class="nav-part-btn" data-part="${pi}">${label}<small>${done}/${ids.length}</small></button>
        <div class="nav-nums">${nums}</div></div>`;
    }).join('');
  }

  function isAnswered(id) {
    const v = state.answers[id];
    return Array.isArray(v) ? v.some(x => x && String(x).trim()) : !!(v && String(v).trim());
  }

  function markFlags() {
    $$('.q-item, .blank-wrap').forEach(el => {
      const id = +(el.id || '').replace('q-', '');
      el.classList.toggle('flagged', state.flags.has(id));
    });
  }

  function gotoPart(pi, keepScroll) {
    if (pi < 0 || pi >= parts().length) return;
    if (state.module === 'reading' && state.passageCache !== null) state.passageCache[state.partIdx] = $('#pane-a').innerHTML;
    const changed = pi !== state.partIdx;
    state.partIdx = pi;
    renderPaneA(); renderQuestions(); renderNav();
    if (changed && state.module === 'listening' && state.mode === 'study') loadStudyAudio();
    if (!keepScroll) $('#pane-b').scrollTop = 0;
  }

  function gotoQuestion(id, focus) {
    const info = state.index[id];
    if (!info) return;
    if (info.pi !== state.partIdx) gotoPart(info.pi, true);
    let el = document.getElementById('q-' + id);
    if (!el) el = $(`.qgroup[data-group]`, $('#pane-b')) && $$('.qgroup').find(g => { const [x, y] = g.dataset.group.split('-').map(Number); return id >= x && id <= y; });
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.classList.add('pulse'); setTimeout(() => el.classList.remove('pulse'), 1200);
    state.focusQ = id; renderNav();
    if (focus) { const inp = $('input, select', el); if (inp && !inp.disabled) inp.focus({ preventScroll: true }); }
  }

  // ---------------------------------------------------------------- 作答
  function onAnswerInput(e) {
    const t = e.target;
    if (t.dataset.multi) {
      const ids = t.dataset.multi.split(',').map(Number);
      const boxes = $$(`input[data-multi="${t.dataset.multi}"]`);
      const chosen = boxes.filter(x => x.checked).map(x => x.value);
      if (chosen.length > ids.length) { t.checked = false; toast(`本题最多选择 ${ids.length} 项`); return; }
      ids.forEach((id, i) => { state.answers[id] = chosen[i] || ''; });
      boxes.forEach(x => x.closest('.opt').classList.toggle('selected', x.checked));
      state.focusQ = ids[0];
    } else if (t.dataset.q) {
      const id = +t.dataset.q;
      if (t.dataset.sub !== undefined) {
        const info = state.index[id];
        const n = (info && info.q.blanks) || 2;
        let arr = Array.isArray(state.answers[id]) ? state.answers[id].slice() : new Array(n).fill('');
        arr[+t.dataset.sub] = t.value;
        state.answers[id] = arr;
      } else {
        state.answers[id] = t.value;
      }
      if (t.type === 'radio') $$(`input[name="${t.name}"]`).forEach(x => x.closest('.opt').classList.toggle('selected', x.checked));
      state.focusQ = id;
    } else return;
    saveProgress();
    renderNav();
  }

  function toggleFlag() {
    const id = state.focusQ;
    if (!id) { toast('先点一下要标记的题目'); return; }
    if (state.flags.has(id)) state.flags.delete(id); else state.flags.add(id);
    saveProgress(); renderNav(); markFlags();
  }

  function step(delta) {
    const i = state.order.indexOf(state.focusQ);
    const next = state.order[i < 0 ? 0 : Math.min(state.order.length - 1, Math.max(0, i + delta))];
    gotoQuestion(next, true);
  }

  // ---------------------------------------------------------------- 判分
  function checkOne(q, g, value) {
    if (g.type === 'multi_choice') return null; // 由组判分处理
    const kind = CHOICE_TYPES.includes(g.type) ? 'choice' : 'text';
    return S.checkQuestion(q, value, { kind, limit: g.limit });
  }

  function gradeGroup(g) {
    const items = [];
    if (g.type === 'multi_choice') {
      const ids = g.questions.map(q => q.id);
      const sel = ids.map(id => state.answers[id]).filter(Boolean);
      const res = S.checkMultiChoice(g, sel);
      // 选对的字母排在前面，逐行显示“第 i 个选择”是否正确
      const keySet = new Set((g.answer_set || []).map(x => String(x).toUpperCase()));
      const picks = sel.slice().sort((x, y) => keySet.has(y.toUpperCase()) - keySet.has(x.toUpperCase()));
      ids.forEach((id, i) => items.push({ id, q: g.questions[i], g, correct: res[i], reason: picks[i] ? '' : 'empty', user: picks[i] || '', key: (g.answer_set || []).join(', ') + '（顺序不限）' }));
      return items;
    }
    g.questions.forEach(q => {
      const r = checkOne(q, g, state.answers[q.id]);
      items.push({ id: q.id, q, g, correct: r.correct, reason: r.reason || '', user: state.answers[q.id], key: S.formatAnswer(q) });
    });
    return items;
  }

  function gradeAll() {
    const items = [];
    parts().forEach((p, pi) => p.groups.forEach(g => gradeGroup(g).forEach(it => items.push(Object.assign(it, { pi })))));
    items.sort((a, b) => a.id - b.id);
    const raw = items.filter(i => i.correct).length;
    const band = S.bandScore(raw, state.module, state.data.variant);
    const byCat = {};
    items.forEach(i => {
      const c = i.g.category || i.g.type;
      byCat[c] = byCat[c] || { total: 0, correct: 0 };
      byCat[c].total++; if (i.correct) byCat[c].correct++;
    });
    return { items, raw, band, byCat, total: items.length };
  }

  const userText = (v) => Array.isArray(v) ? v.filter(Boolean).join(' / ') : (v || '');
  const reasonText = (r) => ({ empty: '未作答', limit: '超出字数限制', incomplete: '两空需都填写' }[r] || '');

  function checkGroupInStudy(groupKey) {
    const p = part();
    const g = p.groups.find(x => x.range.join('-') === groupKey);
    if (!g) return;
    const items = gradeGroup(g);
    items.forEach(it => {
      const el = document.getElementById('q-' + it.id);
      if (el) { el.classList.toggle('is-right', it.correct); el.classList.toggle('is-wrong', !it.correct); }
    });
    const box = document.getElementById('result-' + groupKey);
    box.hidden = false;
    box.innerHTML = items.map(it => {
      const tools = [];
      if (state.module === 'listening' && typeof it.q.t === 'number') tools.push(`<button class="btn tiny" data-act="listen" data-t="${it.q.t}">▶ 听原文</button>`);
      if (state.module === 'reading' && it.q.evidence) tools.push(`<button class="btn tiny" data-act="locate" data-q="${it.id}">定位原文</button>`);
      return `<div class="res-row ${it.correct ? 'ok' : 'bad'}">
        <span class="qnum">${it.id}</span>
        <span class="res-mark">${it.correct ? '✓' : '×'}</span>
        <span class="res-user">你的答案：<b>${esc(userText(it.user)) || '—'}</b>${it.reason ? ` <em>${reasonText(it.reason)}</em>` : ''}</span>
        <span class="res-key">参考答案：<b>${esc(it.key)}</b></span>
        <span class="res-tools">${tools.join('')}</span>
        ${it.q.explanation ? `<div class="res-exp">${R.inline(it.q.explanation)}</div>` : ''}
      </div>`;
    }).join('');
  }

  // 阅读：定位原文证据句
  function locateEvidence(id) {
    const info = state.index[id];
    if (!info || !info.q.evidence) return;
    $$('mark.evidence').forEach(unwrap);
    const body = $('.passage-body');
    if (!body) return;
    const range = findTextRange(body, info.q.evidence);
    if (!range) { toast('未在原文中找到对应句子'); return; }
    const marks = wrapRange(range, 'evidence');
    if (marks[0]) marks[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function findTextRange(root, needle) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = []; let text = '';
    while (walker.nextNode()) { nodes.push({ n: walker.currentNode, start: text.length }); text += walker.currentNode.nodeValue; }
    const norm = (s) => s.replace(/\s+/g, ' ');
    const idx = norm(text).indexOf(norm(needle));
    if (idx < 0) return null;
    // 由于 norm 只压缩空白，这里按原始文本再找一次以拿到准确偏移
    let pos = text.indexOf(needle);
    if (pos < 0) pos = idx;
    const end = pos + needle.length;
    const range = document.createRange();
    let setStart = false;
    for (const { n, start } of nodes) {
      const len = n.nodeValue.length;
      if (!setStart && pos >= start && pos <= start + len) { range.setStart(n, pos - start); setStart = true; }
      if (setStart && end >= start && end <= start + len) { range.setEnd(n, end - start); return range; }
    }
    return null;
  }

  // ---------------------------------------------------------------- 高亮
  function wrapRange(range, cls) {
    const marks = [];
    const root = range.commonAncestorContainer.nodeType === 1 ? range.commonAncestorContainer : range.commonAncestorContainer.parentNode;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const targets = [];
    while (walker.nextNode()) { const n = walker.currentNode; if (range.intersectsNode(n) && n.nodeValue.trim()) targets.push(n); }
    targets.forEach(n => {
      if (n.parentNode.closest('input,select,textarea,button')) return;
      let s = 0, e = n.nodeValue.length;
      if (n === range.startContainer) s = range.startOffset;
      if (n === range.endContainer) e = range.endOffset;
      if (s >= e) return;
      let node = n;
      if (s > 0) node = node.splitText(s);
      if (e - s < node.nodeValue.length) node.splitText(e - s);
      const m = document.createElement('mark');
      m.className = cls;
      node.parentNode.insertBefore(m, node); m.appendChild(node);
      marks.push(m);
    });
    return marks;
  }
  function unwrap(m) {
    const p = m.parentNode; if (!p) return;
    while (m.firstChild) p.insertBefore(m.firstChild, m);
    p.removeChild(m); p.normalize();
  }
  function initHighlight() {
    const bar = $('#hl-toolbar');
    let saved = null;
    document.addEventListener('mouseup', (e) => {
      if (bar.contains(e.target)) return;
      setTimeout(() => {
        const sel = window.getSelection();
        if (!sel.rangeCount || sel.isCollapsed || !sel.toString().trim()) { bar.hidden = true; return; }
        const r = sel.getRangeAt(0);
        const host = (r.commonAncestorContainer.nodeType === 1 ? r.commonAncestorContainer : r.commonAncestorContainer.parentNode);
        if (!host.closest('#pane-a, #pane-b') || host.closest('input,select,textarea')) { bar.hidden = true; return; }
        saved = r.cloneRange();
        const rect = r.getBoundingClientRect();
        bar.style.top = Math.max(8, rect.top - 42) + 'px';
        bar.style.left = Math.max(8, rect.left + rect.width / 2 - 70) + 'px';
        bar.hidden = false;
      }, 0);
    });
    bar.addEventListener('mousedown', e => e.preventDefault());
    bar.addEventListener('click', (e) => {
      const act = e.target.dataset.hl;
      if (act === 'add' && saved) wrapRange(saved, 'hl');
      if (act === 'clear') $$('mark.hl, mark.evidence').forEach(unwrap);
      window.getSelection().removeAllRanges(); bar.hidden = true;
    });
    document.addEventListener('click', (e) => {
      const m = e.target.closest && e.target.closest('mark.hl');
      if (m && !window.getSelection().toString()) unwrap(m);
    });
  }

  // ---------------------------------------------------------------- 音频
  function partAudioUrl(p) { return p && p.audio ? '/media/' + p.audio : ''; }
  function stopAudio() { try { audio.pause(); } catch (_) { /* ignore */ } audio.onended = null; }
  function audioError(msg) {
    const box = $('#pb-error');
    box.hidden = false;
    box.innerHTML = msg;
  }
  function clearAudioError() { $('#pb-error').hidden = true; }

  function loadStudyAudio() {
    const p = part();
    clearAudioError();
    state.ab = null; $('#pb-ab').classList.remove('on'); $('#pb-ab').textContent = 'AB 循环';
    audio.src = partAudioUrl(p);
    audio.playbackRate = +$('#pb-rate').value;
    audio.load();
    if (p.audio_start) audio.addEventListener('loadedmetadata', () => { audio.currentTime = p.audio_start; }, { once: true });
  }

  function renderPlayerbar() {
    const bar = $('#playerbar');
    bar.hidden = state.module !== 'listening';
    $('#pb-study').hidden = state.mode !== 'study';
    $('#pb-mock').hidden = state.mode !== 'mock';
    $('#pb-transcript').classList.toggle('on', state.showTranscript);
  }

  function onTimeUpdate() {
    const p = state.mode === 'mock' ? parts()[state.mockPart] : part();
    if (!p) return;
    const start = p.audio_start || 0;
    const end = p.audio_end || audio.duration || 0;
    const cur = audio.currentTime - start, dur = end - start;
    if (p.audio_end && audio.currentTime >= p.audio_end) { audio.pause(); if (audio.onended) audio.onended(); return; }
    if (state.mode === 'study') {
      $('#pb-cur').textContent = fmt(cur); $('#pb-dur').textContent = fmt(dur);
      if (!seeking) $('#pb-seek').value = dur ? Math.round(cur / dur * 1000) : 0;
      if (state.ab && state.ab.b !== undefined && audio.currentTime >= state.ab.b) audio.currentTime = state.ab.a;
      highlightTranscript();
    } else if (state.phase === 'running' && audio.src) {
      $('#pb-mock-text').textContent = `Part ${p.number} 播放中 · ${fmt(cur)} / ${fmt(dur)}（录音只播放一次，不能暂停或回放）`;
      if (state.phase === 'running') updateTimerUI();
      const sess = Store.get(mockKey(), null);
      if (sess && Math.abs((sess.audioTime || 0) - audio.currentTime) > 2) { sess.audioTime = audio.currentTime; sess.part = state.mockPart; Store.set(mockKey(), sess); }
    }
  }
  let seeking = false;

  function highlightTranscript() {
    if (!state.showTranscript) return;
    const segs = $$('.tr-seg');
    if (!segs.length) return;
    const t = audio.currentTime;
    let active = null;
    for (const el of segs) { if (+el.dataset.start <= t + 0.05) active = el; else break; }
    segs.forEach(el => el.classList.toggle('active', el === active));
    if (active && $('#pane-a').dataset.follow !== '0') {
      const pane = $('#pane-a'), r = active.getBoundingClientRect(), pr = pane.getBoundingClientRect();
      if (r.top < pr.top + 40 || r.bottom > pr.bottom - 40) pane.scrollTop += r.top - pr.top - pr.height / 3;
    }
  }

  function probeDurations() {
    state.durations = [];
    return Promise.all(parts().map((p, i) => new Promise(res => {
      if (p.audio_end) { state.durations[i] = p.audio_end - (p.audio_start || 0); return res(); }
      const a = new Audio(); a.preload = 'metadata'; a.src = partAudioUrl(p);
      a.onloadedmetadata = () => { state.durations[i] = a.duration - (p.audio_start || 0); res(); };
      a.onerror = () => { state.durations[i] = null; res(); };
    })));
  }

  // ---------------------------------------------------------------- 练习模式
  function startPractice() {
    state.phase = 'practice';
    state.elapsed = Store.get(`elapsed:${state.testId}:${state.module}`, 0);
    state.paused = false;
    $('#btn-timer-pause').hidden = false; $('#btn-timer-pause').textContent = '暂停';
    hideOverlay();
    renderAll();
    if (state.module === 'listening') loadStudyAudio();
    startTick();
  }

  // ---------------------------------------------------------------- 模考模式
  function prepareMock() {
    state.phase = 'ready';
    $('#btn-timer-pause').hidden = true;
    const sess = Store.get(mockKey(), null);
    if (!(sess && (sess.phase === 'running' || sess.phase === 'review'))) {
      state.answers = {}; state.flags = new Set(); saveProgress();
    }
    renderAll();
    state.remaining = state.module === 'reading' ? READING_SECONDS : 0;
    updateTimerUI();
    showStartOverlay(sess && (sess.phase === 'running' || sess.phase === 'review') ? sess : null);
  }

  function showStartOverlay(resume) {
    const meta = state.entry.modules[state.module];
    const isL = state.module === 'listening';
    const rules = isL ? [
      '4 个 Part 连续播放，录音<b>只播放一次</b>，不能暂停、拖动或回放。',
      '每个 Part 开始前录音里会留出读题时间；可以随时切换查看其他 Part 的题目。',
      `录音结束后有 <b>${LISTENING_REVIEW_SECONDS / 60} 分钟</b>检查时间（机考规则，无纸笔誊写时间），时间到自动交卷。`,
      '填空题请注意字数限制，超出字数直接判错；拼写须正确，大小写不限。'
    ] : [
      '共 3 篇文章、40 题，限时 <b>60 分钟</b>，时间到自动交卷。',
      '左侧文章可选中文字高亮；拖动中间分隔条可调整宽度。',
      '剩余 10 分钟和 5 分钟时会提醒。'
    ];
    let warn = '';
    if (!state.data.verified) warn += '<div class="alert warn">⚠️ 这套题标记为“未核对”，题目或答案可能有误。</div>';
    if (isL && !meta.audio_ok) warn += `<div class="alert bad">❌ 找不到这套题的音频（${esc(meta.audio_missing.join(', '))}）。<br>请确认 <code>听力/</code> 目录下有对应的 zip 或 mp3（命名规则见 docs 导入指南，识别不了可写 <code>听力/audio_map.json</code>），然后重启程序。<br>可运行 <code>python tools/prepare_media.py --check</code> 查看识别结果。</div>`;
    const canStart = !(isL && !meta.audio_ok);
    $('#overlay-card').innerHTML = `
      <div class="ov-kicker">全真模考 · Computer-delivered IELTS</div>
      <h2>${esc(state.entry.label)} · ${isL ? 'Listening 听力' : (state.data.variant === 'general' ? 'General Training Reading 阅读' : 'Academic Reading 阅读')}</h2>
      <ul class="ov-rules">${rules.map(r => `<li>${r}</li>`).join('')}</ul>
      ${warn}
      <div class="ov-actions">
        ${resume ? `<button class="btn primary" data-ov="resume"${canStart ? '' : ' disabled'}>继续上次未完成的考试</button><button class="btn ghost" data-ov="restart"${canStart ? '' : ' disabled'}>放弃并重新开始</button>`
        : `<button class="btn primary big" data-ov="start"${canStart ? '' : ' disabled'}>开始考试</button>`}
        <button class="btn ghost" data-ov="study">切换到日常练习</button>
      </div>`;
    $('#overlay').hidden = false;
    $('#overlay-card').onclick = (e) => {
      const act = e.target.dataset.ov;
      if (!act) return;
      if (act === 'study') { setMode('study'); return; }
      if (act === 'restart') { Store.remove(mockKey()); state.answers = {}; state.flags = new Set(); saveProgress(); renderAll(); beginMock(null); return; }
      beginMock(act === 'resume' ? resume : null);
    };
  }
  function hideOverlay() { $('#overlay').hidden = true; }

  async function beginMock(resume) {
    hideOverlay();
    state.phase = resume ? resume.phase : 'running';
    const sess = resume || { phase: 'running', startedAt: Date.now(), part: 0, audioTime: 0, remaining: state.module === 'reading' ? READING_SECONDS : null };
    Store.set(mockKey(), sess, true);
    renderQuestions();
    if (state.module === 'reading') {
      state.remaining = sess.remaining || READING_SECONDS;
      startTick();
      return;
    }
    await probeDurations();
    if (state.phase === 'review') { state.remaining = sess.remaining || LISTENING_REVIEW_SECONDS; enterReview(true); return; }
    playMockPart(sess.part || 0, sess.audioTime || 0);
    startTick();
  }

  function playMockPart(i, at) {
    const p = parts()[i];
    state.mockPart = i;
    if (state.partIdx !== i) gotoPart(i);
    clearAudioError();
    audio.src = partAudioUrl(p);
    audio.playbackRate = 1;
    audio.onended = () => {
      if (state.phase !== 'running') return;
      if (i + 1 < parts().length) { toast(`Part ${parts()[i + 1].number} 开始`); playMockPart(i + 1, 0); }
      else enterReview();
    };
    const startAt = (p.audio_start || 0) + (at || 0);
    audio.addEventListener('loadedmetadata', () => { if (startAt) audio.currentTime = startAt; }, { once: true });
    audio.play().catch(err => audioError(`音频无法播放：${esc(err.message)}。请点击 <button class="btn tiny" id="pb-retry">重试</button>`));
    const sess = Store.get(mockKey(), {}); sess.part = i; sess.audioTime = startAt; Store.set(mockKey(), sess, true);
  }

  function enterReview(resumed) {
    stopAudio();
    state.phase = 'review';
    if (!resumed) state.remaining = LISTENING_REVIEW_SECONDS;
    $('#pb-mock-text').textContent = '录音已结束 · 检查时间';
    const sess = Store.get(mockKey(), {}); sess.phase = 'review'; sess.remaining = state.remaining; Store.set(mockKey(), sess, true);
    toast(`录音结束，你有 ${LISTENING_REVIEW_SECONDS / 60} 分钟检查答案`, 4000);
    startTick();
  }

  // ---------------------------------------------------------------- 计时
  function startTick() {
    stopTick();
    updateTimerUI();
    state.tick = setInterval(onTick, 1000);
  }
  function stopTick() { if (state.tick) clearInterval(state.tick); state.tick = null; }
  function onTick() {
    if (state.mode === 'study') {
      if (state.paused) return;
      state.elapsed++;
      if (state.elapsed % 5 === 0) Store.set(`elapsed:${state.testId}:${state.module}`, state.elapsed);
      updateTimerUI();
      return;
    }
    if (state.module === 'reading' && state.phase === 'running' || state.phase === 'review') {
      state.remaining--;
      const sess = Store.get(mockKey(), null);
      if (sess) { sess.remaining = state.remaining; Store.set(mockKey(), sess); }
      if (state.module === 'reading' && (state.remaining === 600 || state.remaining === 300)) toast(`还剩 ${state.remaining / 60} 分钟`, 4000);
      updateTimerUI();
      if (state.remaining <= 0) { stopTick(); toast('时间到，自动交卷'); submit(true); }
    }
  }
  function updateTimerUI() {
    const label = $('#timer-label'), val = $('#timer-value'), box = $('#timer');
    box.classList.remove('warn');
    if (state.mode === 'study') { label.textContent = '练习用时'; val.textContent = fmt(state.elapsed); return; }
    if (state.phase === 'ready') { label.textContent = state.module === 'reading' ? '考试时间' : '听力约'; val.textContent = state.module === 'reading' ? fmt(READING_SECONDS) : '30:00'; return; }
    if (state.phase === 'finished') { label.textContent = '已交卷'; val.textContent = '--:--'; return; }
    if (state.module === 'reading' || state.phase === 'review') {
      label.textContent = state.phase === 'review' ? '检查时间' : '剩余时间';
      val.textContent = fmt(state.remaining);
      if (state.remaining <= 300) box.classList.add('warn');
      return;
    }
    // 听力播放中：剩余 = 当前 Part 剩余 + 后续 Part 时长 + 检查时间
    const p = parts()[state.mockPart];
    const curDur = state.durations[state.mockPart] || 0;
    const cur = audio.currentTime - ((p && p.audio_start) || 0);
    let rest = Math.max(0, curDur - cur);
    for (let i = state.mockPart + 1; i < parts().length; i++) rest += state.durations[i] || 0;
    label.textContent = '剩余时间';
    val.textContent = fmt(rest + LISTENING_REVIEW_SECONDS);
  }

  // ---------------------------------------------------------------- 交卷与报告
  function submit(auto) {
    if (state.mode === 'mock' && state.phase === 'ready') { toast('请先开始考试'); return; }
    const unanswered = state.order.filter(id => !isAnswered(id)).length;
    if (!auto && state.mode === 'mock' && !confirm(`确定交卷吗？${unanswered ? `还有 ${unanswered} 题未作答。` : ''}`)) return;
    const res = gradeAll();
    const used = state.mode === 'study' ? state.elapsed
      : (state.module === 'reading' ? READING_SECONDS - Math.max(0, state.remaining) : null);
    const record = {
      id: Date.now(), date: new Date().toISOString(), testId: state.testId, label: state.entry.label,
      module: state.module, mode: state.mode, raw: res.raw, total: res.total, band: res.band, used,
      byCat: res.byCat,
      wrong: res.items.filter(i => !i.correct).map(i => ({ id: i.id, cat: i.g.category || i.g.type, user: userText(i.user), key: i.key, reason: i.reason }))
    };
    const hist = Store.get('history', []); hist.unshift(record); Store.set('history', hist.slice(0, 500), true);
    if (state.mode === 'mock') {
      stopTick(); stopAudio();
      state.phase = 'finished';
      Store.remove(mockKey());
      // 练习模式还没做过这套题时，把模考答案复制过去，方便逐组复盘（不覆盖已有练习进度）
      const studyKey = `progress:${state.testId}:${state.module}:study`;
      const prev = Store.get(studyKey, null);
      if (!prev || !Object.keys(prev.answers || {}).length) Store.set(studyKey, { answers: state.answers, flags: Array.from(state.flags), updated: Date.now() }, true);
      renderQuestions(); updateTimerUI();
      $('#pb-mock-text').textContent = '已交卷';
    }
    state.lastReport = { res, record };
    showReport(res, record);
  }

  function showReport(res, record, filter) {
    filter = filter || 'all';
    const acc = Math.round(res.raw / res.total * 100);
    const cats = Object.entries(res.byCat).map(([c, v]) => `<tr><td>${esc(CATEGORY[c] || c)}</td><td>${v.correct} / ${v.total}</td><td><div class="bar"><i style="width:${Math.round(v.correct / v.total * 100)}%"></i></div></td></tr>`).join('');
    const rows = res.items.filter(i => filter === 'all' || !i.correct).map(i => `
      <tr class="${i.correct ? 'ok' : 'bad'}">
        <td><span class="qnum">${i.id}</span></td><td>${esc(CATEGORY[i.g.category] || i.g.category || i.g.type)}</td>
        <td>${esc(userText(i.user)) || '<span class="muted">未作答</span>'}${i.reason === 'limit' ? ' <em>超字数</em>' : ''}</td>
        <td><b>${esc(i.key)}</b></td><td>${i.correct ? '✓' : '×'}</td>
      </tr>`).join('');
    $('#report-body').innerHTML = `
      <div class="rep-top">
        <div class="rep-band"><small>Band</small><b>${res.band.toFixed(1)}</b></div>
        <div class="rep-stats">
          <div><small>原始分</small><b>${res.raw} / ${res.total}</b></div>
          <div><small>正确率</small><b>${acc}%</b></div>
          <div><small>用时</small><b>${record.used !== null && record.used !== undefined ? fmt(record.used) : '—'}</b></div>
          <div><small>模式</small><b>${state.mode === 'mock' ? '全真模考' : '日常练习'}</b></div>
        </div>
      </div>
      <p class="muted small">${esc(record.label)} · ${state.module === 'listening' ? '听力' : (state.data.variant === 'general' ? '培训类阅读' : '学术类阅读')}。分数按剑桥公布的近似换算表计算，每次真实考试会有 ±0.5 分左右的浮动。</p>
      <h3>按题型统计</h3>
      <table class="rep-cats">${cats}</table>
      <div class="rep-filter">
        <h3>逐题明细</h3>
        <button class="btn small ${filter === 'all' ? 'primary' : 'ghost'}" data-rep="all">全部</button>
        <button class="btn small ${filter === 'wrong' ? 'primary' : 'ghost'}" data-rep="wrong">只看错题 (${res.items.filter(i => !i.correct).length})</button>
        <span class="spacer"></span>
        <button class="btn small" data-rep="csv">导出错题 CSV</button>
        ${state.mode === 'mock' ? '<button class="btn small primary" data-rep="review">进入练习模式复盘</button>' : ''}
      </div>
      <table class="rep-table"><thead><tr><th>题号</th><th>题型</th><th>你的答案</th><th>参考答案</th><th></th></tr></thead><tbody>${rows}</tbody></table>`;
    $('#modal-report').hidden = false;
    $('#report-body').onclick = (e) => {
      const a = e.target.dataset.rep;
      if (a === 'all' || a === 'wrong') showReport(res, record, a);
      if (a === 'csv') exportCSV([record], `错题_${record.testId}_${record.module}_${record.id}.csv`);
      if (a === 'review') { $('#modal-report').hidden = true; setMode('study'); }
    };
  }

  function showHistory() {
    const hist = Store.get('history', []);
    const rows = hist.map(h => `<tr>
      <td>${esc(new Date(h.date).toLocaleString())}</td><td>${esc(h.label)}</td><td>${h.module === 'listening' ? '听力' : '阅读'}</td>
      <td>${h.mode === 'mock' ? '模考' : '练习'}</td><td>${h.raw}/${h.total}</td><td><b>${(+h.band).toFixed(1)}</b></td>
      <td>${h.used !== null && h.used !== undefined ? fmt(h.used) : '—'}</td><td>${h.wrong.length}</td></tr>`).join('');
    // 题型弱项汇总
    const agg = {};
    hist.forEach(h => Object.entries(h.byCat || {}).forEach(([c, v]) => { agg[c] = agg[c] || { t: 0, c: 0 }; agg[c].t += v.total; agg[c].c += v.correct; }));
    const weak = Object.entries(agg).sort((a, b) => a[1].c / a[1].t - b[1].c / b[1].t)
      .map(([c, v]) => `<tr><td>${esc(CATEGORY[c] || c)}</td><td>${v.c} / ${v.t}</td><td><div class="bar"><i style="width:${Math.round(v.c / v.t * 100)}%"></i></div></td></tr>`).join('');
    $('#history-body').innerHTML = hist.length ? `
      <h3>题型正确率（全部记录，从弱到强）</h3><table class="rep-cats">${weak}</table>
      <div class="rep-filter"><h3>做题记录</h3><span class="spacer"></span><button class="btn small" data-h="csv">导出全部错题 CSV</button><button class="btn small ghost" data-h="clear">清空记录</button></div>
      <table class="rep-table"><thead><tr><th>时间</th><th>套题</th><th>科目</th><th>模式</th><th>原始分</th><th>Band</th><th>用时</th><th>错题</th></tr></thead><tbody>${rows}</tbody></table>`
      : '<div class="empty small">还没有记录。交卷后会自动保存成绩。</div>';
    $('#modal-history').hidden = false;
    $('#history-body').onclick = (e) => {
      if (e.target.dataset.h === 'csv') exportCSV(hist, `错题汇总_${new Date().toISOString().slice(0, 10)}.csv`);
      if (e.target.dataset.h === 'clear' && confirm('确定清空全部历史成绩？')) { Store.set('history', [], true); showHistory(); }
    };
  }

  async function exportCSV(records, filename) {
    const cell = (v) => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const lines = [['日期', '套题', '科目', '模式', '题号', '题型', '你的答案', '参考答案', '备注'].map(cell).join(',')];
    records.forEach(r => r.wrong.forEach(w => lines.push([
      r.date.slice(0, 10), r.label, r.module === 'listening' ? '听力' : '阅读', r.mode === 'mock' ? '模考' : '练习',
      w.id, CATEGORY[w.cat] || w.cat, w.user, w.key, reasonText(w.reason)
    ].map(cell).join(','))));
    const content = '\ufeff' + lines.join('\r\n');
    try {
      const r = await fetch('/api/export', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ filename, content }) });
      if (!r.ok) throw new Error(r.status);
      const j = await r.json();
      toast('已导出到 ' + j.path, 5000);
    } catch (e) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([content], { type: 'text/csv' }));
      a.download = filename; a.click();
    }
  }

  // ---------------------------------------------------------------- 模式切换
  function setMode(mode) {
    if (mode === state.mode) return;
    if (!confirmLeaveMock()) return;
    state.mode = mode;
    load();
  }
  function confirmLeaveMock() {
    if (state.mode === 'mock' && (state.phase === 'running' || state.phase === 'review')) {
      return confirm('模考正在进行。离开后进度会保留，下次可以继续。确定离开吗？');
    }
    return true;
  }
  function setFont(f) {
    document.body.classList.remove('font-s', 'font-m', 'font-l');
    document.body.classList.add('font-' + f);
    const p = Store.get('prefs', {}); p.font = f; Store.set('prefs', p);
  }

  // ---------------------------------------------------------------- 事件
  function bindEvents() {
    $('#test-select').addEventListener('change', (e) => {
      if (!confirmLeaveMock()) { e.target.value = state.testId; return; }
      state.testId = e.target.value; load();
    });
    $('#module-seg').addEventListener('click', (e) => {
      const m = e.target.closest('button') && e.target.closest('button').dataset.module;
      if (!m || m === state.module || !confirmLeaveMock()) return;
      state.module = m; load();
    });
    $('#mode-seg').addEventListener('click', (e) => {
      const m = e.target.closest('button') && e.target.closest('button').dataset.mode;
      if (m) setMode(m);
    });
    $('#btn-submit').addEventListener('click', () => submit(false));
    $('#btn-history').addEventListener('click', showHistory);
    $('#btn-font').addEventListener('click', () => {
      const order = ['s', 'm', 'l'];
      const cur = order.find(f => document.body.classList.contains('font-' + f)) || 'm';
      setFont(order[(order.indexOf(cur) + 1) % 3]);
    });
    $('#btn-timer-pause').addEventListener('click', () => {
      state.paused = !state.paused;
      $('#btn-timer-pause').textContent = state.paused ? '继续' : '暂停';
    });
    $('#btn-flag').addEventListener('click', toggleFlag);
    $('#btn-prev').addEventListener('click', () => step(-1));
    $('#btn-next').addEventListener('click', () => step(1));
    $('#nav-parts').addEventListener('click', (e) => {
      const q = e.target.closest('[data-q]');
      if (q) { gotoQuestion(+q.dataset.q, true); return; }
      const p = e.target.closest('[data-part]');
      if (p) gotoPart(+p.dataset.part);
    });
    const pb = $('#pane-b');
    pb.addEventListener('input', onAnswerInput);
    pb.addEventListener('change', (e) => { if (e.target.matches('select, input[type=radio], input[type=checkbox]')) onAnswerInput(e); });
    pb.addEventListener('focusin', (e) => {
      const id = e.target.dataset && (e.target.dataset.q || (e.target.dataset.multi || '').split(',')[0]);
      if (id) { state.focusQ = +id; renderNav(); }
    });
    pb.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-act]');
      if (!btn) {
        const item = e.target.closest('.q-item'); if (item) { state.focusQ = +item.id.replace('q-', ''); renderNav(); }
        return;
      }
      if (btn.dataset.act === 'check-group') checkGroupInStudy(btn.dataset.group);
      if (btn.dataset.act === 'locate') locateEvidence(+btn.dataset.q);
      if (btn.dataset.act === 'listen') { audio.currentTime = Math.max(0, +btn.dataset.t - 3); audio.play(); }
    });
    $('#pane-a').addEventListener('click', (e) => {
      const seg = e.target.closest('.tr-seg');
      if (seg && state.mode === 'study') { audio.currentTime = +seg.dataset.start; audio.play(); }
    });
    $('#pane-a').addEventListener('wheel', () => { $('#pane-a').dataset.follow = '0'; clearTimeout(window.__followT); window.__followT = setTimeout(() => { $('#pane-a').dataset.follow = '1'; }, 4000); }, { passive: true });

    // 播放器（练习模式）
    $('#pb-play').addEventListener('click', () => { if (audio.paused) audio.play().catch(err => audioError('音频无法播放：' + esc(err.message))); else audio.pause(); });
    $$('[data-seek]').forEach(b => b.addEventListener('click', () => { audio.currentTime = Math.max(0, audio.currentTime + (+b.dataset.seek)); }));
    const seek = $('#pb-seek');
    seek.addEventListener('input', () => { seeking = true; });
    seek.addEventListener('change', () => {
      const p = part(), start = p.audio_start || 0, end = p.audio_end || audio.duration || 0;
      audio.currentTime = start + (end - start) * (+seek.value / 1000); seeking = false;
    });
    $('#pb-rate').addEventListener('change', (e) => { audio.playbackRate = +e.target.value; });
    $('#pb-vol').addEventListener('input', (e) => { audio.volume = +e.target.value; });
    $('#pb-ab').addEventListener('click', () => {
      const b = $('#pb-ab');
      if (!state.ab) { state.ab = { a: audio.currentTime }; b.textContent = 'A ' + fmt(audio.currentTime) + ' → 设 B'; b.classList.add('on'); }
      else if (state.ab.b === undefined) {
        if (audio.currentTime <= state.ab.a + 0.5) { toast('B 点需要在 A 点之后'); return; }
        state.ab.b = audio.currentTime; b.textContent = `循环 ${fmt(state.ab.a)}–${fmt(state.ab.b)} ×`;
      } else { state.ab = null; b.textContent = 'AB 循环'; b.classList.remove('on'); }
    });
    $('#pb-transcript').addEventListener('click', () => { state.showTranscript = !state.showTranscript; renderPlayerbar(); renderPaneA(); });
    $('#playerbar').addEventListener('click', (e) => { if (e.target.id === 'pb-retry') { clearAudioError(); audio.play().catch(() => {}); } });
    audio.addEventListener('timeupdate', onTimeUpdate);
    ['loadedmetadata', 'durationchange', 'emptied', 'seeked'].forEach(ev => audio.addEventListener(ev, onTimeUpdate));
    audio.addEventListener('play', () => { $('#pb-play').textContent = '⏸ 暂停'; });
    audio.addEventListener('pause', () => { $('#pb-play').textContent = '▶ 播放'; });
    audio.addEventListener('error', () => {
      if (!audio.getAttribute('src')) return;
      const p = state.mode === 'mock' ? parts()[state.mockPart] : part();
      audioError(`找不到或无法读取音频 <code>media/${esc(p && p.audio)}</code>。请确认 <code>听力/</code> 下有对应 zip，重启程序会自动解压；也可以手动运行 <code>python tools/prepare_media.py</code>。`);
    });

    // 弹窗
    $$('[data-close]').forEach(b => b.addEventListener('click', () => { b.closest('.modal').hidden = true; }));
    $$('.modal').forEach(m => m.addEventListener('click', (e) => { if (e.target === m) m.hidden = true; }));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') $$('.modal').forEach(m => { m.hidden = true; }); });
    initHighlight();
    initResizer();
    window.addEventListener('beforeunload', () => { if (state.mode === 'study') Store.set(`elapsed:${state.testId}:${state.module}`, state.elapsed, true); });
  }

  function initResizer() {
    const rz = $('#resizer'), main = $('#main'), a = $('#pane-a');
    let drag = false;
    rz.addEventListener('mousedown', (e) => { drag = true; document.body.classList.add('resizing'); e.preventDefault(); });
    document.addEventListener('mousemove', (e) => {
      if (!drag) return;
      const r = main.getBoundingClientRect();
      let pct = (e.clientX - r.left) / r.width * 100;
      if (document.body.classList.contains('mod-listening')) pct = 100 - pct; // 听力原文在右侧
      pct = Math.min(70, Math.max(25, pct));
      a.style.flexBasis = pct + '%';
    });
    document.addEventListener('mouseup', () => { drag = false; document.body.classList.remove('resizing'); });
  }

  window.IELTSApp = { state, gradeAll, load };
  document.addEventListener('DOMContentLoaded', init);
})();
