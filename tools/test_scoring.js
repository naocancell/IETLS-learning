// 判分逻辑单元测试：node tools/test_scoring.js
const S = require('../ielts_client/web/js/scoring.js');
let pass = 0, fail = 0;
function eq(name, got, want) {
  if (JSON.stringify(got) === JSON.stringify(want)) { pass++; }
  else { fail++; console.error(`✗ ${name}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`); }
}
const text = (answer, v, limit, extra) => S.checkQuestion(Object.assign({ answer }, extra || {}), v, { kind: 'text', limit }).correct;
const choice = (answer, v) => S.checkQuestion({ answer }, v, { kind: 'choice' }).correct;
const L3N = { words: 3, number: true }, L2 = { words: 2, number: false };

// 旧版 bug 回归：TFNG 永远判错
eq('TFNG FALSE', choice(['FALSE'], 'FALSE'), true);
eq('TFNG NOT GIVEN', choice(['NOT GIVEN'], 'NOT GIVEN'), true);
eq('TFNG wrong', choice(['TRUE'], 'FALSE'), false);
// 旧版 bug 回归：子串匹配误判
eq('substring ent', text(['student newspaper'], 'ent', L3N), false);
eq('partial coal', text(['coal and firewood'], 'coal', L3N), false);
eq('extra words', text(['American Museum'], 'the American Museum and Bath', L3N), false);
// 括号可省略
eq('optional the', text(['(the) Tower of London'], 'tower of london', L3N), true);
eq('optional the 2', text(['(the) Tower of London'], 'The Tower of London', null), true);
// 加上 the 后共 4 个词，超过 NO MORE THAN THREE WORDS，按真实考试判错
eq('the + 3 words over limit', text(['(the) Tower of London'], 'The Tower of London', L3N), false);
eq('plural (s)', text(['(the) freshwater dolphin(s)'], 'freshwater dolphins', L3N), true);
eq('plural (s) 2', text(['(the) freshwater dolphin(s)'], 'freshwater dolphin', L3N), true);
eq('optional main', text(['(main) Workshop'], 'Main workshop', L2), true);
// 大小写 / 末尾标点 / 重音 / 引号
eq('case+period', text(['Yentob'], ' yentob. ', L3N), true);
eq('accent', text(['Cafe', 'Café'], 'café', L2), true);
eq('spelling must be exact', text(['Yentob'], 'Yentop', L3N), false);
// 日期格式
eq('date 1', text(['13th February'], '13 February', L3N), true);
eq('date 2', text(['13th February'], 'February 13th', L3N), true);
eq('date 3', text(['13th February'], 'the 13th of February', L3N), true);
eq('date wrong', text(['13th February'], '16th February', L3N), false);
// 数字千分位
eq('thousand sep', text(['1500'], '1,500', L3N), true);
// 字数限制
eq('limit 2 words', text(['considerably reduce'], 'considerably reduce', L2), true);
eq('over limit', text(['space', 'room'], 'more space room', L2), false);
eq('number not counted', text(['more than 12'], 'more than 12', L3N), true);
eq('limit reason', S.checkQuestion({ answer: ['x'] }, 'a b c', { kind: 'text', limit: L2 }).reason, 'limit');
// 一题两空，顺序不限
const two = { answer: [['coal'], ['firewood']], blanks: 2, any_order: true };
eq('two blanks', S.checkQuestion(two, ['coal', 'firewood'], { kind: 'text', limit: L3N }).correct, true);
eq('two blanks reversed', S.checkQuestion(two, ['Firewood', 'coal'], { kind: 'text', limit: L3N }).correct, true);
eq('two blanks one missing', S.checkQuestion(two, ['coal', ''], { kind: 'text', limit: L3N }).correct, false);
// Choose TWO 多选
eq('multi 2 hits', S.checkMultiChoice({ questions: [21, 22], answer_set: ['B', 'D'] }, ['D', 'B']), [true, true]);
eq('multi 1 hit', S.checkMultiChoice({ questions: [21, 22], answer_set: ['B', 'D'] }, ['A', 'B']), [true, false]);
// 分数换算
eq('band L 30', S.bandScore(30, 'listening'), 7);
eq('band L 32', S.bandScore(32, 'listening'), 7.5);
eq('band R 33', S.bandScore(33, 'reading', 'academic'), 7.5);
eq('band R 27', S.bandScore(27, 'reading'), 6.5);
eq('band GT 30', S.bandScore(30, 'reading', 'general'), 6);

console.log(`scoring tests: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
