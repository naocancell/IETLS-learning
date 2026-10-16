/*
 * IELTS Master - 判分与分数换算（纯函数，无 DOM 依赖，可在 Node 中单测）
 *
 * 答案写法约定（与剑桥官方答案页一致）：
 *   - 每个可接受答案单独作为数组的一项：["notice board", "noticeboard"]
 *   - 括号内为可省略部分："(the) Tower of London"、"freshwater dolphin(s)"
 *   - 多空题（一题两空，如 "coal ... and ... firewood"）：answer 为二维数组，
 *     配合 any_order: true 表示顺序不限，两空都对才得 1 分
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.IELTSScoring = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july',
    'august', 'september', 'october', 'november', 'december'];
  const MONTH_ALIAS = {};
  MONTHS.forEach((m, i) => { MONTH_ALIAS[m] = i + 1; MONTH_ALIAS[m.slice(0, 3)] = i + 1; });
  MONTH_ALIAS.sept = 9;

  /** 统一大小写、引号、连字符、重音与空白 */
  function normalize(s) {
    if (s === null || s === undefined) return '';
    let t = String(s).normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
    t = t.toLowerCase().trim()
      .replace(/[\u2018\u2019\u02bc`´]/g, "'")
      .replace(/[\u201c\u201d]/g, '"')
      .replace(/[\u2010-\u2015\u2212]/g, '-')
      .replace(/(\d),(?=\d{3}\b)/g, '$1')          // 1,500 -> 1500
      .replace(/\s*-\s*/g, '-')
      .replace(/["]/g, '')
      .replace(/[.,;:!?]+$/g, '')                  // 末尾标点
      .replace(/^[.,;:!?]+/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    t = t.replace(/-/g, ' ').replace(/\s+/g, ' ');  // well-known == well known
    return normalizeDate(t);
  }

  /** "13th February" / "13 Feb" / "February 13th" / "the 13th of February" -> "13 february" */
  function normalizeDate(t) {
    const m1 = t.match(/^(?:the )?(\d{1,2})(?:st|nd|rd|th)?(?: of)? ([a-z]+)$/);
    const m2 = t.match(/^([a-z]+) (?:the )?(\d{1,2})(?:st|nd|rd|th)?$/);
    let day, mon;
    if (m1 && MONTH_ALIAS[m1[2]]) { day = +m1[1]; mon = MONTH_ALIAS[m1[2]]; }
    else if (m2 && MONTH_ALIAS[m2[1]]) { day = +m2[2]; mon = MONTH_ALIAS[m2[1]]; }
    if (day && mon && day <= 31) return day + ' ' + MONTHS[mon - 1];
    return t;
  }

  /** 展开括号可省略写法："(the) Tower of London" -> ["the tower of london", "tower of london"] */
  function expandPattern(pattern) {
    const parts = [];
    const re = /\(([^)]*)\)/g;
    let last = 0, m;
    while ((m = re.exec(pattern)) !== null) {
      parts.push({ fixed: pattern.slice(last, m.index) });
      parts.push({ optional: m[1] });
      last = re.lastIndex;
    }
    parts.push({ fixed: pattern.slice(last) });
    let variants = [''];
    for (const p of parts) {
      if (p.fixed !== undefined) variants = variants.map(v => v + p.fixed);
      else variants = variants.flatMap(v => [v + p.optional, v]);
      if (variants.length > 64) break;
    }
    return Array.from(new Set(variants.map(normalize).filter(Boolean)));
  }

  function acceptedSet(list) {
    const set = new Set();
    (list || []).forEach(p => expandPattern(String(p)).forEach(v => set.add(v)));
    return set;
  }

  /**
   * 统计字数：连字符词算 1 个词；当题目允许 "AND/OR A NUMBER" 时，
   * 数字（含 1,500 / 8.30 / 3rd / £15 等）单独计，不占单词名额。
   */
  function countWords(answer, allowNumber) {
    const tokens = String(answer || '').trim().split(/\s+/).filter(Boolean);
    let words = 0, numbers = 0;
    for (const tk of tokens) {
      if (/^[£$€]?\d[\d,.:/]*(st|nd|rd|th|%|am|pm|a\.m\.|p\.m\.)?$/i.test(tk)) numbers++;
      else words++;
    }
    if (!allowNumber) return { words: words + numbers, numbers: 0 };
    return { words, numbers };
  }

  function violatesLimit(answer, limit) {
    if (!limit || !limit.words) return false;
    const c = countWords(answer, limit.number);
    if (c.words > limit.words) return true;
    if (limit.number && c.numbers > 1) return true;
    return false;
  }

  function matchText(user, acceptedList) {
    const u = normalize(user);
    if (!u) return false;
    return acceptedSet(acceptedList).has(u);
  }

  /**
   * 判一道题。
   * @param {object} q     题目对象（含 answer / blanks / any_order）
   * @param {string|string[]} value 用户答案
   * @param {object} ctx   { kind: 'text'|'choice', limit: {words, number} }
   * @returns {{correct: boolean, reason?: string}}
   */
  function checkQuestion(q, value, ctx) {
    ctx = ctx || {};
    const empty = v => v === undefined || v === null || String(v).trim() === '';
    if (Array.isArray(value) ? value.every(empty) : empty(value)) return { correct: false, reason: 'empty' };

    if (ctx.kind === 'choice') {
      const u = String(value).trim().toUpperCase();
      return { correct: (q.answer || []).some(a => String(a).trim().toUpperCase() === u) };
    }

    const blanks = q.blanks || 1;
    if (blanks === 1) {
      const v = Array.isArray(value) ? value[0] : value;
      if (violatesLimit(v, ctx.limit)) return { correct: false, reason: 'limit' };
      return { correct: matchText(v, q.answer) };
    }

    const vals = Array.isArray(value) ? value : [value];
    if (vals.some(v => violatesLimit(v, ctx.limit))) return { correct: false, reason: 'limit' };
    const keys = q.answer || [];
    if (vals.length < blanks || vals.some(empty)) return { correct: false, reason: 'incomplete' };
    const direct = keys.every((k, i) => matchText(vals[i], k));
    if (direct) return { correct: true };
    if (q.any_order) {
      for (const perm of permutations(vals.slice(0, blanks))) {
        if (keys.every((k, i) => matchText(perm[i], k))) return { correct: true };
      }
    }
    return { correct: false };
  }

  function permutations(arr) {
    if (arr.length <= 1) return [arr];
    const out = [];
    arr.forEach((x, i) => {
      permutations(arr.slice(0, i).concat(arr.slice(i + 1))).forEach(p => out.push([x].concat(p)));
    });
    return out;
  }

  /**
   * "Choose TWO letters" 类多选题：每选中一个正确字母得 1 分，不计顺序。
   * 返回与 group.questions 顺序对应的布尔数组。
   */
  function checkMultiChoice(group, selected) {
    const set = new Set((group.answer_set || []).map(s => String(s).toUpperCase()));
    const picked = Array.from(new Set((selected || []).map(s => String(s).toUpperCase())));
    const hits = picked.filter(s => set.has(s)).length;
    return group.questions.map((_, i) => i < hits);
  }

  /** 题组答案格式化为可读字符串 */
  function formatAnswer(q) {
    const a = q.answer || [];
    if ((q.blanks || 1) > 1) {
      return a.map(x => x.join(' / ')).join(q.any_order ? ' + ' : ' ; ') + (q.any_order ? '（顺序不限）' : '');
    }
    return a.join(' / ');
  }

  // 剑桥官方公布的近似换算（Listening / Academic Reading / General Training Reading）
  const BAND_TABLES = {
    listening: [[39, 9], [37, 8.5], [35, 8], [32, 7.5], [30, 7], [26, 6.5], [23, 6], [18, 5.5], [16, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5], [0, 0]],
    academic: [[39, 9], [37, 8.5], [35, 8], [33, 7.5], [30, 7], [27, 6.5], [23, 6], [19, 5.5], [15, 5], [13, 4.5], [10, 4], [8, 3.5], [6, 3], [4, 2.5], [0, 0]],
    general: [[40, 9], [39, 8.5], [38, 8], [36, 7.5], [34, 7], [32, 6.5], [30, 6], [27, 5.5], [23, 5], [19, 4.5], [15, 4], [12, 3.5], [8, 3], [5, 2.5], [0, 0]]
  };

  function bandScore(raw, module, variant) {
    const key = module === 'listening' ? 'listening' : (variant === 'general' ? 'general' : 'academic');
    for (const [min, band] of BAND_TABLES[key]) if (raw >= min) return band;
    return 0;
  }

  return { normalize, expandPattern, countWords, violatesLimit, matchText, checkQuestion, checkMultiChoice, formatAnswer, bandScore, BAND_TABLES };
});
