/*
 * IELTS Master - 轻量标记渲染 + 题组渲染
 *
 * 题库里的 passage / template / instruction 使用一个很小的 Markdown 子集：
 *   # 标题 / ## 小标题          段落之间空一行；段内换行保留
 *   - 列表（两个空格缩进 = 二级列表）
 *   | a | b |  表格（第二行为 |---| 时第一行是表头）；单元格内可用 <br>
 *   > 引用/示例框        ![说明](img/xxx.png) 图片（相对套题目录）
 *   **粗体**  *斜体*     {{12}} 第 12 题填空；{{11.1}} {{11.2}} 一题两空
 */
(function (global) {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ctx: { blank(qid, sub) -> html, imgBase }
  function inline(text, ctx) {
    let h = esc(text);
    h = h.replace(/&lt;br\s*\/?&gt;/g, '<br>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/(^|[^*])\*([^*\s][^*]*?)\*/g, '$1<i>$2</i>');
    h = h.replace(/\{\{(\d+)(?:\.(\d+))?\}\}/g, (_, q, sub) =>
      ctx && ctx.blank ? ctx.blank(+q, sub ? +sub - 1 : null) : `[${q}]`);
    return h;
  }

  function markup(src, ctx) {
    ctx = ctx || {};
    const blocks = String(src || '').replace(/\r/g, '').split(/\n\s*\n/);
    const out = [];
    for (const raw of blocks) {
      const block = raw.replace(/^\n+|\n+$/g, '');
      if (!block.trim()) continue;
      const lines = block.split('\n');
      const first = lines[0];
      if (/^#\s/.test(first) && lines.length === 1) { out.push(`<h3 class="mk-h1">${inline(first.slice(2), ctx)}</h3>`); continue; }
      if (/^##\s/.test(first) && lines.length === 1) { out.push(`<h4 class="mk-h2">${inline(first.slice(3), ctx)}</h4>`); continue; }
      const img = first.match(/^!\[(.*?)\]\((.+?)\)$/);
      if (img && lines.length === 1) {
        const srcUrl = (ctx.imgBase || '') + img[2];
        out.push(`<figure class="mk-fig"><img src="${esc(srcUrl)}" alt="${esc(img[1])}">${img[1] ? `<figcaption>${inline(img[1], ctx)}</figcaption>` : ''}</figure>`);
        continue;
      }
      if (lines.every(l => /^\s*\|/.test(l))) { out.push(table(lines, ctx)); continue; }
      if (lines.every(l => /^\s*-\s/.test(l))) { out.push(list(lines, ctx)); continue; }
      if (lines.every(l => /^>\s?/.test(l))) {
        out.push(`<div class="mk-note">${lines.map(l => inline(l.replace(/^>\s?/, ''), ctx)).join('<br>')}</div>`);
        continue;
      }
      // 混合块：标题行 + 列表等，逐行处理
      if (lines.some(l => /^\s*-\s/.test(l))) {
        let buf = [], html = '';
        const flushList = () => { if (buf.length) { html += list(buf, ctx); buf = []; } };
        for (const l of lines) {
          if (/^\s*-\s/.test(l)) buf.push(l);
          else { flushList(); html += `<p>${inline(l, ctx)}</p>`; }
        }
        flushList();
        out.push(html);
        continue;
      }
      const label = first.match(/^\[([A-Z])\]\s+/);
      if (label) {
        out.push(`<p class="mk-labelled"><span class="para-label">${label[1]}</span>${inline(block.slice(label[0].length), ctx).replace(/\n/g, '<br>')}</p>`);
        continue;
      }
      out.push(`<p>${lines.map(l => inline(l, ctx)).join('<br>')}</p>`);
    }
    return out.join('\n');
  }

  function list(lines, ctx) {
    let html = '<ul class="mk-list">', depth = 0;
    for (const l of lines) {
      const d = Math.floor((l.match(/^\s*/)[0].length) / 2);
      const text = l.replace(/^\s*-\s/, '');
      while (depth < d) { html += '<ul class="mk-list">'; depth++; }
      while (depth > d) { html += '</ul>'; depth--; }
      html += `<li>${inline(text, ctx)}</li>`;
    }
    while (depth > 0) { html += '</ul>'; depth--; }
    return html + '</ul>';
  }

  function table(lines, ctx) {
    const rows = lines.map(l => l.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(c => c.trim()));
    const hasHead = rows.length > 1 && rows[1].every(c => /^:?-{3,}:?$/.test(c));
    let html = '<div class="mk-table-wrap"><table class="mk-table">';
    rows.forEach((r, i) => {
      if (hasHead && i === 1) return;
      const tag = hasHead && i === 0 ? 'th' : 'td';
      html += '<tr>' + r.map(c => `<${tag}>${inline(c, ctx)}</${tag}>`).join('') + '</tr>';
    });
    return html + '</table></div>';
  }

  // ---------------- 题组渲染 ----------------
  const TFNG = ['TRUE', 'FALSE', 'NOT GIVEN'];
  const YNNG = ['YES', 'NO', 'NOT GIVEN'];

  /**
   * @param group  题组对象
   * @param opt    { answers, imgBase, study, disabled }
   */
  function renderGroup(group, opt) {
    const [a, b] = group.range;
    const ctx = makeCtx(group, opt);
    let h = `<section class="qgroup" data-group="${a}-${b}">`;
    h += `<h3 class="qg-title">Questions ${a}${b !== a ? '–' + b : ''}</h3>`;
    if (group.instruction) h += `<div class="qg-instr">${markup(group.instruction.split('\n').join('\n\n'), ctx)}</div>`;
    if (group.image) h += `<figure class="qg-image"><img src="${esc(opt.imgBase + group.image)}" alt="Questions ${a}-${b}"></figure>`;
    if (group.options && !group.select_inline && group.type !== 'single_choice') h += optionsBox(group);
    if (group.options && group.select_inline) h += optionsBox(group, true);
    if (group.example) h += `<div class="qg-example"><span class="tag">Example</span>${markup(group.example.split('\n').join('<br>'), ctx)}</div>`;
    if (group.title) h += `<h4 class="qg-subtitle">${inline(group.title, ctx)}</h4>`;

    const t = group.type;
    if (group.template) {
      h += `<div class="qg-template">${markup(group.template, ctx)}</div>`;
    } else if (t === 'completion') {
      h += group.questions.map(q => {
        const p = q.prompt && /\{\{/.test(q.prompt) ? q.prompt : `${q.prompt || ''} {{${q.id}}}`;
        return `<div class="q-item" id="q-${q.id}">${inline(p, ctx).replace(/<span class="blank-wrap/, '<span class="blank-wrap')}</div>`;
      }).join('');
    } else if (t === 'single_choice') {
      h += group.questions.map(q => choiceItem(q, q.options, opt, 'radio')).join('');
    } else if (t === 'tfng' || t === 'ynng') {
      const labels = t === 'tfng' ? TFNG : YNNG;
      h += group.questions.map(q => choiceItem(q, labels.map(l => ({ key: l, text: '' })), opt, 'radio', true)).join('');
    } else if (t === 'multi_choice') {
      h += multiItem(group, opt);
    } else if (t === 'matching') {
      h += group.questions.map(q => `<div class="q-item q-match" id="q-${q.id}"><span class="qnum">${q.id}</span><span class="q-prompt">${inline(q.prompt || '', ctx)}</span>${ctx.select(q.id)}</div>`).join('');
    }
    if (opt.study) h += `<div class="qg-tools"><button class="btn small" data-act="check-group" data-group="${a}-${b}">核对本组答案</button><div class="qg-result" id="result-${a}-${b}" hidden></div></div>`;
    return h + '</section>';
  }

  function makeCtx(group, opt) {
    const ans = opt.answers || {};
    const dis = opt.disabled ? ' disabled' : '';
    const selectHtml = (qid) => {
      const cur = ans[qid] || '';
      const opts = (group.options || []).map(o => `<option value="${esc(o.key)}"${cur === o.key ? ' selected' : ''}>${esc(group.select_inline ? o.text : o.key)}</option>`).join('');
      return `<select class="q-select" data-q="${qid}" aria-label="Question ${qid}"${dis}><option value="">${qid}</option>${opts}</select>`;
    };
    return {
      imgBase: opt.imgBase,
      select: selectHtml,
      blank(qid, sub) {
        if (group.select_inline) return `<span class="blank-wrap" id="q-${qid}">${selectHtml(qid)}</span>`;
        const v = ans[qid];
        const val = sub === null ? (Array.isArray(v) ? v[0] : v) : (Array.isArray(v) ? v[sub] : (sub === 0 ? v : ''));
        const idAttr = sub === null || sub === 0 ? ` id="q-${qid}"` : '';
        const ph = sub === null ? String(qid) : `${qid}`;
        return `<span class="blank-wrap"${idAttr}><input class="blank" type="text" autocomplete="off" spellcheck="false" data-q="${qid}"${sub !== null ? ` data-sub="${sub}"` : ''} value="${esc(val || '')}" placeholder="${ph}"${dis}></span>`;
      }
    };
  }

  function optionsBox(group, words) {
    const title = group.options_title ? `<div class="ob-title">${esc(group.options_title)}</div>` : '';
    if (words) return `<div class="options-box words">${title}${group.options.map(o => `<span class="word">${esc(o.text)}</span>`).join('')}</div>`;
    return `<div class="options-box">${title}${group.options.map(o => `<div class="ob-row"><b>${esc(o.key)}</b><span>${esc(o.text)}</span></div>`).join('')}</div>`;
  }

  function choiceItem(q, options, opt, kind, compact) {
    const cur = (opt.answers || {})[q.id] || '';
    const dis = opt.disabled ? ' disabled' : '';
    const prompt = q.prompt ? `<div class="q-prompt">${inline(q.prompt)}</div>` : '';
    const opts = (options || []).map(o => `
      <label class="opt${cur === o.key ? ' selected' : ''}${compact ? ' compact' : ''}">
        <input type="${kind}" name="q${q.id}" data-q="${q.id}" value="${esc(o.key)}"${cur === o.key ? ' checked' : ''}${dis}>
        <b>${esc(o.key)}</b>${o.text ? `<span>${inline(o.text)}</span>` : ''}
      </label>`).join('');
    return `<div class="q-item q-choice${compact ? ' q-tf' : ''}" id="q-${q.id}"><div class="q-head"><span class="qnum">${q.id}</span>${prompt}</div><div class="opts${compact ? ' row' : ''}">${opts}</div></div>`;
  }

  function multiItem(group, opt) {
    const ids = group.questions.map(q => q.id);
    const ans = opt.answers || {};
    const chosen = ids.map(id => ans[id]).filter(Boolean);
    const dis = opt.disabled ? ' disabled' : '';
    const opts = group.options.map(o => `
      <label class="opt${chosen.includes(o.key) ? ' selected' : ''}">
        <input type="checkbox" data-multi="${ids.join(',')}" value="${esc(o.key)}"${chosen.includes(o.key) ? ' checked' : ''}${dis}>
        <b>${esc(o.key)}</b><span>${inline(o.text)}</span>
      </label>`).join('');
    return `<div class="q-item q-choice" id="q-${ids[0]}"><div class="q-head"><span class="qnum">${ids.join('–')}</span><div class="q-prompt">${inline(group.prompt || '')}</div></div><div class="opts">${opts}</div></div>`;
  }

  global.IELTSRender = { esc, inline, markup, renderGroup };
})(window);
