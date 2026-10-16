// IELTS Master - 核心前端交互与业务逻辑

let appMode = 'mock'; // 'mock' (全真模考) | 'study' (刷题精听精读)
let currentModule = 'listening'; // 'listening' | 'reading'
let currentPartIndex = 0; // 0, 1, 2, 3 (Sections 1-4 或 Passages 1-3)
let userAnswers = { listening: {}, reading: {} };
let reviewedQuestions = { listening: new Set(), reading: new Set() };
let examTimerSeconds = 30 * 60; // 听力 30 分钟，阅读 60 分钟
let timerInterval = null;
let isTimerPaused = false;
let currentExamData = window.EXAM_DATA || { listening: { sections: [] }, reading: { passages: [] } };
let showChineseTranscript = true;

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
  loadSavedAnswers();
  initDragResizer();
  initHighlightToolbar();
  initAudioEvents();
  renderCurrentModule();
  startTimer();
});

// 本地存储读取
function loadSavedAnswers() {
  try {
    const saved = localStorage.getItem('ielts_user_answers');
    if (saved) {
      userAnswers = JSON.parse(saved);
      if (!userAnswers.listening) userAnswers.listening = {};
      if (!userAnswers.reading) userAnswers.reading = {};
    }
  } catch (e) {
    console.warn('LocalStorage unavailable');
  }
}

function saveAnswers() {
  try {
    localStorage.setItem('ielts_user_answers', JSON.stringify(userAnswers));
  } catch (e) {}
}

// 模式切换
function switchAppMode(mode) {
  appMode = mode;
  const btnMock = document.getElementById('btn-mode-mock');
  const btnStudy = document.getElementById('btn-mode-study');
  const studyBar = document.getElementById('study-control-bar');
  const timerLabel = document.getElementById('timer-label');
  const timerPauseBtn = document.getElementById('btn-timer-pause');

  if (mode === 'mock') {
    btnMock.className = 'px-3 py-1.5 rounded-md font-medium transition-all flex items-center space-x-1.5 bg-red-600 text-white shadow-sm';
    btnStudy.className = 'px-3 py-1.5 rounded-md font-medium transition-all flex items-center space-x-1.5 text-slate-300 hover:text-white';
    studyBar.classList.add('hidden');
    timerLabel.textContent = '考试倒计时:';
    timerPauseBtn.classList.add('hidden');
    // 全真模考重设倒计时
    resetExamTimer();
  } else {
    btnStudy.className = 'px-3 py-1.5 rounded-md font-medium transition-all flex items-center space-x-1.5 bg-indigo-600 text-white shadow-sm';
    btnMock.className = 'px-3 py-1.5 rounded-md font-medium transition-all flex items-center space-x-1.5 text-slate-300 hover:text-white';
    studyBar.classList.remove('hidden');
    timerLabel.textContent = '练习计时:';
    timerPauseBtn.classList.remove('hidden');
  }

  // 重新渲染题目卡片（刷题模式展示核对按钮）
  renderQuestions();
}

// 科目切换
function switchModule(module) {
  currentModule = module;
  currentPartIndex = 0;

  const tabListening = document.getElementById('tab-listening');
  const tabReading = document.getElementById('tab-reading');

  if (module === 'listening') {
    tabListening.className = 'px-3 py-1 text-xs font-semibold rounded bg-amber-500 text-slate-950 shadow';
    tabReading.className = 'px-3 py-1 text-xs font-semibold rounded bg-slate-800 text-slate-300 hover:bg-slate-700';
    examTimerSeconds = 30 * 60;
  } else {
    tabReading.className = 'px-3 py-1 text-xs font-semibold rounded bg-amber-500 text-slate-950 shadow';
    tabListening.className = 'px-3 py-1 text-xs font-semibold rounded bg-slate-800 text-slate-300 hover:bg-slate-700';
    examTimerSeconds = 60 * 60;
    // 切到阅读时暂停音频
    const audio = document.getElementById('global-audio');
    audio.pause();
    updatePlayPauseButton(false);
  }

  resetExamTimer();
  renderCurrentModule();
}

// 重置倒计时
function resetExamTimer() {
  if (timerInterval) clearInterval(timerInterval);
  if (currentModule === 'listening') {
    examTimerSeconds = 30 * 60;
  } else {
    examTimerSeconds = 60 * 60;
  }
  updateTimerDisplay();
  startTimer();
}

function startTimer() {
  if (timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    if (isTimerPaused) return;
    if (appMode === 'mock') {
      if (examTimerSeconds > 0) {
        examTimerSeconds--;
        updateTimerDisplay();
      } else {
        clearInterval(timerInterval);
        alert('考试时间到！系统将为您自动交卷并计算成绩。');
        submitExam();
      }
    } else {
      examTimerSeconds++;
      updateTimerDisplay();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const m = Math.floor(examTimerSeconds / 60).toString().padStart(2, '0');
  const s = (examTimerSeconds % 60).toString().padStart(2, '0');
  document.getElementById('exam-timer').textContent = `${m}:${s}`;
}

function toggleTimer() {
  isTimerPaused = !isTimerPaused;
  const btn = document.getElementById('btn-timer-pause');
  btn.textContent = isTimerPaused ? '继续' : '暂停';
}

// 渲染当前科目主视图
function renderCurrentModule() {
  renderPartTabs();
  renderLeftPane();
  renderQuestions();
  renderNavGrid();
  updateAnsweredStats();

  if (currentModule === 'listening') {
    loadPartAudio();
  }
}

// 渲染底部 Part 标签栏
function renderPartTabs() {
  const container = document.getElementById('part-tabs-container');
  container.innerHTML = '';

  const parts = currentModule === 'listening' 
    ? currentExamData.listening.sections 
    : currentExamData.reading.passages;

  parts.forEach((part, idx) => {
    const btn = document.createElement('button');
    const label = currentModule === 'listening' ? `Part ${idx + 1}` : `Passage ${idx + 1}`;
    const isActive = idx === currentPartIndex;

    btn.className = `px-3 py-1 rounded text-xs font-bold transition ${
      isActive 
        ? 'bg-blue-600 text-white shadow' 
        : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300'
    }`;
    btn.textContent = label;
    btn.onclick = () => {
      currentPartIndex = idx;
      renderCurrentModule();
    };
    container.appendChild(btn);
  });
}

// 渲染左侧面板（文章或听力引导）
function renderLeftPane() {
  const badge = document.getElementById('left-pane-badge');
  const title = document.getElementById('left-pane-title');
  const content = document.getElementById('left-pane-content');

  if (currentModule === 'listening') {
    const section = currentExamData.listening.sections[currentPartIndex];
    badge.textContent = `Section ${section.section_number}`;
    badge.className = 'bg-blue-600 text-white px-2 py-0.5 rounded text-[11px]';
    title.textContent = section.title;

    let html = `
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-xs text-blue-900 mb-4 leading-relaxed">
        <div class="font-bold mb-1 flex items-center space-x-1">
          <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <span>官方听力考场指引 (Listening Instructions)</span>
        </div>
        <p>${section.instruction.replace(/\n/g, '<br>')}</p>
      </div>
      <div class="bg-white border border-gray-200 rounded-lg p-5 shadow-sm space-y-4">
        <h3 class="font-bold text-gray-900 border-b border-gray-100 pb-2 text-sm">${section.title}</h3>
        <div class="font-mono text-xs whitespace-pre-wrap leading-relaxed text-gray-700 bg-gray-50 p-4 rounded border border-gray-200">${section.intro_text}</div>
      </div>
    `;

    // 刷题模式下，左侧可以直接展示精听原文
    if (appMode === 'study' && section.transcript) {
      html += `
        <div class="mt-6 border-t border-gray-200 pt-4">
          <div class="flex items-center justify-between mb-3">
            <h4 class="font-bold text-xs text-indigo-900 flex items-center space-x-1">
              <span>🎧 本节听力完整录音原文 (精听定位):</span>
            </h4>
          </div>
          <div class="space-y-3 text-xs">
            ${renderTranscriptHTML(section.transcript)}
          </div>
        </div>
      `;
    }

    content.innerHTML = html;
  } else {
    // 阅读文章
    const passage = currentExamData.reading.passages[currentPartIndex];
    badge.textContent = `Passage ${passage.passage_number}`;
    badge.className = 'bg-emerald-600 text-white px-2 py-0.5 rounded text-[11px]';
    title.textContent = passage.title;

    let paragraphs = passage.content.split('\n\n');
    let html = `
      <div class="mb-4 bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-900">
        <p class="font-semibold">${passage.instruction}</p>
      </div>
      <article class="space-y-3 text-gray-800 leading-relaxed font-serif text-[15px]">
        <h2 class="text-lg font-bold text-gray-900 font-sans mb-3">${passage.title}</h2>
        ${paragraphs.map((p, i) => `<p class="passage-paragraph" data-para="${i}">${p}</p>`).join('')}
      </article>
    `;
    content.innerHTML = html;
  }

  // 恢复滚动条置顶
  content.scrollTop = 0;
}

// 渲染听力原文片段
function renderTranscriptHTML(transcript) {
  return transcript.map(t => {
    let hlBadge = '';
    if (t.highlight_q && t.highlight_q.length > 0) {
      hlBadge = t.highlight_q.map(q => 
        `<span onclick="scrollToQuestion(${q})" class="inline-block bg-amber-400 text-slate-950 px-1.5 py-0.5 rounded font-bold cursor-pointer hover:bg-amber-300 ml-1.5 text-[10px]">考点定位 Q${q}</span>`
      ).join('');
    }

    return `
      <div class="p-2.5 rounded border border-gray-200 bg-gray-50 hover:bg-amber-50/50 transition">
        <div class="flex items-center justify-between text-[11px] text-gray-500 font-bold mb-1">
          <span>${t.speaker}</span>
          <div>${hlBadge}</div>
        </div>
        <p class="text-gray-800 leading-relaxed mb-1">${t.en}</p>
        ${showChineseTranscript && t.zh ? `<p class="text-gray-500 text-[11px] border-t border-gray-100 pt-1 leading-normal">${t.zh}</p>` : ''}
      </div>
    `;
  }).join('');
}

// 渲染右侧作答区题目卡片
function renderQuestions() {
  const container = document.getElementById('questions-container');
  const rightInstruction = document.getElementById('right-pane-instruction');
  container.innerHTML = '';

  const part = currentModule === 'listening' 
    ? currentExamData.listening.sections[currentPartIndex] 
    : currentExamData.reading.passages[currentPartIndex];

  rightInstruction.textContent = part.instruction.split('\n')[0] || '请根据左侧内容完成下方作答：';

  part.questions.forEach(q => {
    const card = document.createElement('div');
    card.id = `q-card-${q.q_id}`;
    card.className = 'question-card space-y-3';

    const isReviewed = reviewedQuestions[currentModule].has(q.q_id);
    const curAnswer = userAnswers[currentModule][q.q_id] || '';

    // 头部：题号、复查标记
    let headerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="q-badge">${q.q_id}</span>
          <span class="text-xs text-gray-400">${q.type === 'fill_blank' ? '填空题 (Fill in the blank)' : '选择/判断题'}</span>
        </div>
        <label class="flex items-center space-x-1.5 text-xs text-gray-500 cursor-pointer select-none">
          <input type="checkbox" onchange="toggleReview(${q.q_id}, this.checked)" ${isReviewed ? 'checked' : ''} class="rounded text-yellow-500 focus:ring-0">
          <span>标记复查 (Review)</span>
        </label>
      </div>
    `;

    // 题干与选项
    let bodyHTML = `<div class="text-sm font-medium text-gray-800 leading-relaxed">${q.prompt}</div>`;

    if (q.type === 'fill_blank') {
      bodyHTML += `
        <div class="mt-2">
          <input type="text" class="ielts-input" placeholder="输入答案 (大小写不限)..." 
            value="${escapeHtml(curAnswer)}" 
            oninput="handleInputAnswer(${q.q_id}, this.value)">
        </div>
      `;
    } else {
      // 选择题 / TFNG
      const options = q.options || ['TRUE', 'FALSE', 'NOT GIVEN'];
      bodyHTML += `<div class="grid grid-cols-1 gap-2 mt-2">`;
      options.forEach(opt => {
        const optLetter = opt.trim().charAt(0);
        // 如果选项就是纯文本如 'TRUE'，直接匹配文本；如果是 'A. ...'，匹配选项字母
        const isSelected = curAnswer === opt || curAnswer === optLetter;
        bodyHTML += `
          <button onclick="handleOptionSelect(${q.q_id}, '${optLetter}')" 
            class="option-btn ${isSelected ? 'selected' : ''}">
            <span>${opt}</span>
          </button>
        `;
      });
      bodyHTML += `</div>`;
    }

    // 刷题模式专用：即时核对按钮与题解区
    let studyToolHTML = '';
    if (appMode === 'study') {
      studyToolHTML = `
        <div class="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
          <button onclick="checkSingleQuestion(${q.q_id})" class="px-2.5 py-1 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold rounded border border-indigo-200 transition">
            ✓ 核对答案 (Check)
          </button>
          <div id="q-feedback-${q.q_id}" class="hidden flex-1 ml-3 text-xs p-2 rounded"></div>
        </div>
        <div id="q-explain-${q.q_id}" class="hidden mt-2 p-3 bg-amber-50 rounded-md border border-amber-200 text-xs text-amber-950 leading-relaxed space-y-1">
          <div class="font-bold text-amber-900">💡 官方参考答案: <span class="text-green-700">${q.answers ? q.answers.join(' / ') : ''}</span></div>
          <div><b>考点解析与同义替换:</b> ${q.explanation || '暂无详细解析'}</div>
        </div>
      `;
    }

    card.innerHTML = headerHTML + bodyHTML + studyToolHTML;
    container.appendChild(card);
  });
}

// 底部 40 题导航网格渲染
function renderNavGrid() {
  const grid = document.getElementById('question-nav-grid');
  grid.innerHTML = '';

  for (let i = 1; i <= 40; i++) {
    const btn = document.createElement('button');
    const isAnswered = !!userAnswers[currentModule][i];
    const isReviewed = reviewedQuestions[currentModule].has(i);

    let cls = 'nav-q-btn';
    if (isAnswered) cls += ' answered';
    if (isReviewed) cls += ' reviewed';

    btn.className = cls;
    btn.textContent = i;
    btn.onclick = () => scrollToQuestion(i);
    grid.appendChild(btn);
  }
}

// 作答状态更新统计
function updateAnsweredStats() {
  const answered = Object.keys(userAnswers[currentModule]).filter(k => userAnswers[currentModule][k] && userAnswers[currentModule][k].trim()).length;
  document.getElementById('answered-count').textContent = answered;
}

// 用户输入作答
function handleInputAnswer(qid, val) {
  if (!userAnswers[currentModule]) userAnswers[currentModule] = {};
  userAnswers[currentModule][qid] = val;
  saveAnswers();
  renderNavGrid();
  updateAnsweredStats();
}

// 用户点击选项
function handleOptionSelect(qid, optLetter) {
  if (!userAnswers[currentModule]) userAnswers[currentModule] = {};
  userAnswers[currentModule][qid] = optLetter;
  saveAnswers();
  renderQuestions();
  renderNavGrid();
  updateAnsweredStats();

  // 如果开启了自动即时核对
  if (appMode === 'study' && document.getElementById('chk-auto-check').checked) {
    checkSingleQuestion(qid);
  }
}

// 标记 Review
function toggleReview(qid, isChecked) {
  if (isChecked) {
    reviewedQuestions[currentModule].add(qid);
  } else {
    reviewedQuestions[currentModule].delete(qid);
  }
  renderNavGrid();
}

// 滚动定位到具体题目
function scrollToQuestion(qid) {
  // 先判断该题目属于哪个 Section / Passage
  let targetPartIndex = 0;
  if (currentModule === 'listening') {
    if (qid >= 1 && qid <= 10) targetPartIndex = 0;
    else if (qid >= 11 && qid <= 20) targetPartIndex = 1;
    else if (qid >= 21 && qid <= 30) targetPartIndex = 2;
    else targetPartIndex = 3;
  } else {
    if (qid >= 1 && qid <= 14) targetPartIndex = 0;
    else if (qid >= 15 && qid <= 26) targetPartIndex = 1;
    else targetPartIndex = 2;
  }

  if (targetPartIndex !== currentPartIndex) {
    currentPartIndex = targetPartIndex;
    renderCurrentModule();
  }

  setTimeout(() => {
    const card = document.getElementById(`q-card-${qid}`);
    if (card) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.add('active-target');
      setTimeout(() => card.classList.remove('active-target'), 2000);
    }
  }, 100);
}

// 题号上一题 / 下一题
function prevQuestion() {
  // 查找当前屏幕可视题目的前一题
  const cards = document.querySelectorAll('.question-card');
  if (cards.length > 0) {
    const firstQid = parseInt(cards[0].id.replace('q-card-', ''), 10);
    if (firstQid > 1) scrollToQuestion(firstQid - 1);
  }
}

function nextQuestion() {
  const cards = document.querySelectorAll('.question-card');
  if (cards.length > 0) {
    const lastQid = parseInt(cards[cards.length - 1].id.replace('q-card-', ''), 10);
    if (lastQid < 40) scrollToQuestion(lastQid + 1);
  }
}

// 清空当前科目答题
function resetAnswers() {
  if (confirm('确定要清空当前科目的所有已填答案吗？')) {
    userAnswers[currentModule] = {};
    reviewedQuestions[currentModule].clear();
    saveAnswers();
    renderCurrentModule();
  }
}

// 刷题模式：单题即时核对
function checkSingleQuestion(qid) {
  let qObj = null;
  const parts = currentModule === 'listening' ? currentExamData.listening.sections : currentExamData.reading.passages;
  for (let p of parts) {
    for (let q of p.questions) {
      if (q.q_id === qid) { qObj = q; break; }
    }
    if (qObj) break;
  }

  if (!qObj) return;

  const userAns = (userAnswers[currentModule][qid] || '').trim();
  const isCorrect = verifyAnswer(userAns, qObj.answers);

  const fbEl = document.getElementById(`q-feedback-${qid}`);
  const expEl = document.getElementById(`q-explain-${qid}`);

  if (fbEl && expEl) {
    fbEl.classList.remove('hidden');
    expEl.classList.remove('hidden');

    if (!userAns) {
      fbEl.className = 'text-xs p-1.5 rounded bg-amber-100 text-amber-800 font-bold';
      fbEl.textContent = '未填写答案';
    } else if (isCorrect) {
      fbEl.className = 'text-xs p-1.5 rounded bg-green-100 text-green-800 font-bold flex items-center space-x-1';
      fbEl.innerHTML = `<span>✓ 回答正确！</span>`;
    } else {
      fbEl.className = 'text-xs p-1.5 rounded bg-red-100 text-red-800 font-bold flex items-center space-x-1';
      fbEl.innerHTML = `<span>✗ 回答错误 (你填写的是: "${userAns}")</span>`;
    }
  }
}

// 验证答案容错算法
function verifyAnswer(userAns, standardAnswers) {
  if (!userAns || !standardAnswers || standardAnswers.length === 0) return false;
  const cleanU = userAns.toLowerCase().replace(/[\.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim();

  for (let ans of standardAnswers) {
    const cleanS = ans.toLowerCase().replace(/[\.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").trim();
    if (cleanU === cleanS) return true;
    // 包含关系或单复数轻度容错
    if (cleanU.length > 2 && (cleanS.includes(cleanU) || cleanU.includes(cleanS))) {
      return true;
    }
  }
  return false;
}

// 音频控制器逻辑
function loadPartAudio() {
  const audio = document.getElementById('global-audio');
  const section = currentExamData.listening.sections[currentPartIndex];
  if (section && section.audio_url) {
    audio.src = section.audio_url;
    audio.load();
    if (appMode === 'mock') {
      // 模考模式自动流水播音
      audio.play().catch(() => {});
      updatePlayPauseButton(true);
    }
  }
}

function initAudioEvents() {
  const audio = document.getElementById('global-audio');
  const curTimeEl = document.getElementById('audio-cur-time');
  const totalTimeEl = document.getElementById('audio-total-time');
  const slider = document.getElementById('audio-seek-slider');

  audio.ontimeupdate = () => {
    if (!audio.duration) return;
    const cur = audio.currentTime;
    const dur = audio.duration;
    curTimeEl.textContent = formatTime(cur);
    totalTimeEl.textContent = formatTime(dur);
    slider.value = (cur / dur) * 100;
  };

  audio.onplay = () => updatePlayPauseButton(true);
  audio.onpause = () => updatePlayPauseButton(false);
  audio.onended = () => {
    updatePlayPauseButton(false);
    // 模考模式下自动顺延播放下一个 Part
    if (appMode === 'mock' && currentPartIndex < 3) {
      currentPartIndex++;
      renderCurrentModule();
    }
  };
}

function toggleAudioPlay() {
  const audio = document.getElementById('global-audio');
  if (audio.paused) {
    audio.play();
  } else {
    audio.pause();
  }
}

function updatePlayPauseButton(isPlaying) {
  const btnText = document.getElementById('play-pause-icon');
  if (btnText) {
    btnText.textContent = isPlaying ? '⏸ 暂停' : '▶ 播放';
  }
}

function seekAudio(delta) {
  const audio = document.getElementById('global-audio');
  audio.currentTime = Math.max(0, Math.min(audio.duration || 0, audio.currentTime + delta));
}

function onSeekSliderChange(percent) {
  const audio = document.getElementById('global-audio');
  if (audio.duration) {
    audio.currentTime = (percent / 100) * audio.duration;
  }
}

function changePlaybackRate(rate) {
  const audio = document.getElementById('global-audio');
  audio.playbackRate = parseFloat(rate);
}

function changeVolume(val) {
  const audio = document.getElementById('global-audio');
  audio.volume = parseFloat(val);
}

function formatTime(secs) {
  const m = Math.floor(secs / 60).toString().padStart(2, '0');
  const s = Math.floor(secs % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

// 听力原文抽屉面板
function toggleTranscriptPanel() {
  const drawer = document.getElementById('transcript-drawer');
  const isHidden = drawer.classList.contains('hidden');
  if (isHidden) {
    drawer.classList.remove('hidden');
    renderDrawerTranscript();
  } else {
    drawer.classList.add('hidden');
  }
}

function renderDrawerTranscript() {
  const list = document.getElementById('transcript-list');
  const section = currentExamData.listening.sections[currentPartIndex];
  if (section && section.transcript) {
    list.innerHTML = renderTranscriptHTML(section.transcript);
  } else {
    list.innerHTML = '<div class="text-slate-400 p-4">当前科目非听力，无录音原文。</div>';
  }
}

function toggleTranscriptLang() {
  showChineseTranscript = !showChineseTranscript;
  document.getElementById('btn-toggle-lang').textContent = showChineseTranscript ? '隐藏中文译文' : '显示中文译文';
  renderDrawerTranscript();
  renderLeftPane();
}

// 选词高亮 (Highlight Tool)
function initHighlightToolbar() {
  const leftPane = document.getElementById('left-pane');
  const toolbar = document.getElementById('highlight-toolbar');

  leftPane.addEventListener('mouseup', () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      toolbar.classList.add('hidden');
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    toolbar.style.top = `${rect.top - 36}px`;
    toolbar.style.left = `${rect.left + (rect.width / 2) - 40}px`;
    toolbar.classList.remove('hidden');
  });

  document.addEventListener('mousedown', (e) => {
    if (!toolbar.contains(e.target) && !leftPane.contains(e.target)) {
      toolbar.classList.add('hidden');
    }
  });
}

function applyHighlight() {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;

  const range = selection.getRangeAt(0);
  const mark = document.createElement('mark');
  mark.className = 'ielts-highlight';
  mark.title = '点击移除高亮';
  mark.onclick = (e) => {
    e.stopPropagation();
    const parent = mark.parentNode;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    parent.removeChild(mark);
  };

  try {
    range.surroundContents(mark);
  } catch (e) {
    // 跨段落选区处理
    document.execCommand('hiliteColor', false, '#fef08a');
  }

  selection.removeAllRanges();
  document.getElementById('highlight-toolbar').classList.add('hidden');
}

function clearTextHighlights() {
  const marks = document.querySelectorAll('mark.ielts-highlight');
  marks.forEach(m => {
    const parent = m.parentNode;
    while (m.firstChild) parent.insertBefore(m.firstChild, m);
    parent.removeChild(m);
  });
}

// 可拖拽分栏大小 (Drag Resizer)
function initDragResizer() {
  const resizer = document.getElementById('drag-resizer');
  const leftPane = document.getElementById('left-pane');
  const container = document.getElementById('main-container');
  let isDragging = false;

  resizer.addEventListener('mousedown', (e) => {
    isDragging = true;
    document.body.style.cursor = 'col-resize';
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const containerRect = container.getBoundingClientRect();
    const newWidth = e.clientX - containerRect.left;
    const percent = (newWidth / containerRect.width) * 100;
    if (percent >= 25 && percent <= 75) {
      leftPane.style.width = `${percent}%`;
    }
  });

  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
      document.body.style.cursor = 'default';
    }
  });
}

// 交卷与官方 9 分制评分
function submitExam() {
  const parts = currentModule === 'listening' ? currentExamData.listening.sections : currentExamData.reading.passages;
  let allQuestions = [];
  parts.forEach(p => allQuestions.push(...p.questions));

  let correctCount = 0;
  let wrongCount = 0;
  let reportItems = [];

  allQuestions.forEach(q => {
    const userAns = (userAnswers[currentModule][q.q_id] || '').trim();
    const isCorrect = verifyAnswer(userAns, q.answers);
    if (isCorrect) correctCount++;
    else wrongCount++;

    reportItems.push({
      q_id: q.q_id,
      prompt: q.prompt,
      userAns: userAns || '<未作答>',
      standardAns: q.answers ? q.answers.join(' / ') : '',
      isCorrect: isCorrect,
      explanation: q.explanation || '暂无详细解析'
    });
  });

  // 雅思 9 分制官方换算
  const bandScore = calculateBandScore(correctCount, currentModule);

  // 渲染成绩单
  document.getElementById('report-subtext').textContent = `剑桥雅思 4 - Test 1 ${currentModule === 'listening' ? '听力' : '阅读'}模块评估`;
  document.getElementById('report-band-score').textContent = bandScore.toFixed(1);
  document.getElementById('report-raw-score').textContent = `${correctCount} / 40`;
  document.getElementById('report-accuracy').textContent = `正确率: ${Math.round((correctCount / 40) * 100)}%`;
  document.getElementById('report-error-count').textContent = wrongCount;

  // 用时统计
  let totalAllowed = currentModule === 'listening' ? 30 * 60 : 60 * 60;
  let spent = Math.max(0, totalAllowed - examTimerSeconds);
  let spM = Math.floor(spent / 60);
  let spS = spent % 60;
  document.getElementById('report-time-spent').textContent = `${spM}分${spS}秒`;

  // 渲染明细
  renderReportDetails(reportItems, 'all');

  // 显示弹窗
  document.getElementById('score-modal').classList.remove('hidden');
}

// 官方 9 分制转换表 (Academic)
function calculateBandScore(rawScore, module) {
  if (module === 'listening') {
    if (rawScore >= 39) return 9.0;
    if (rawScore >= 37) return 8.5;
    if (rawScore >= 35) return 8.0;
    if (rawScore >= 32) return 7.5;
    if (rawScore >= 30) return 7.0;
    if (rawScore >= 26) return 6.5;
    if (rawScore >= 23) return 6.0;
    if (rawScore >= 18) return 5.5;
    if (rawScore >= 16) return 5.0;
    if (rawScore >= 13) return 4.5;
    if (rawScore >= 10) return 4.0;
    if (rawScore >= 6) return 3.5;
    return 3.0;
  } else {
    // Academic Reading
    if (rawScore >= 39) return 9.0;
    if (rawScore >= 37) return 8.5;
    if (rawScore >= 35) return 8.0;
    if (rawScore >= 33) return 7.5;
    if (rawScore >= 30) return 7.0;
    if (rawScore >= 27) return 6.5;
    if (rawScore >= 23) return 6.0;
    if (rawScore >= 19) return 5.5;
    if (rawScore >= 15) return 5.0;
    if (rawScore >= 13) return 4.5;
    if (rawScore >= 10) return 4.0;
    if (rawScore >= 6) return 3.5;
    return 3.0;
  }
}

let cachedReportItems = [];
function renderReportDetails(items, filter) {
  cachedReportItems = items;
  const container = document.getElementById('report-details-list');
  container.innerHTML = '';

  const filtered = filter === 'wrong' ? items.filter(i => !i.isCorrect) : items;

  filtered.forEach(item => {
    const card = document.createElement('div');
    card.className = `p-3 rounded-lg border flex flex-col space-y-1.5 ${
      item.isCorrect ? 'bg-green-50/60 border-green-200' : 'bg-red-50/60 border-red-200'
    }`;

    card.innerHTML = `
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="w-6 h-6 rounded flex items-center justify-center font-bold text-xs ${
            item.isCorrect ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }">Q${item.q_id}</span>
          <span class="font-semibold text-gray-800">${escapeHtml(item.prompt)}</span>
        </div>
        <span class="font-bold text-xs ${item.isCorrect ? 'text-green-700' : 'text-red-700'}">
          ${item.isCorrect ? '✓ 得分' : '✗ 错误'}
        </span>
      </div>
      <div class="flex items-center space-x-6 text-xs pl-8">
        <div>你的答案: <b class="${item.isCorrect ? 'text-green-800' : 'text-red-800'}">${escapeHtml(item.userAns)}</b></div>
        <div>官方标准答案: <b class="text-green-700">${item.standardAns}</b></div>
      </div>
      <div class="text-[11px] text-gray-600 bg-white/80 p-2 rounded border border-gray-100 pl-8">
        <b>考点解析:</b> ${item.explanation}
      </div>
    `;
    container.appendChild(card);
  });
}

function filterReport(type) {
  const btnAll = document.getElementById('btn-filter-all');
  const btnWrong = document.getElementById('btn-filter-wrong');

  if (type === 'all') {
    btnAll.className = 'px-2.5 py-1 rounded bg-gray-800 text-white font-medium';
    btnWrong.className = 'px-2.5 py-1 rounded bg-red-100 text-red-700 font-medium';
    renderReportDetails(cachedReportItems, 'all');
  } else {
    btnWrong.className = 'px-2.5 py-1 rounded bg-red-600 text-white font-medium';
    btnAll.className = 'px-2.5 py-1 rounded bg-gray-200 text-gray-800 font-medium';
    renderReportDetails(cachedReportItems, 'wrong');
  }
}

function closeScoreModal() {
  document.getElementById('score-modal').classList.add('hidden');
}

function switchToStudyFromReport() {
  closeScoreModal();
  switchAppMode('study');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
