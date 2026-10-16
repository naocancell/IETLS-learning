# IELTS Master —— 剑桥雅思机考模拟 + 精听精读

本地运行的桌面客户端：按官方机考（CD-IELTS）流程做剑桥雅思真题模考，平时用练习模式精听精读、逐组核对答案、复盘错题。

> 当前题库：**剑4 Test 1（听力 + 学术类阅读）**，题目按原书录入、答案逐题核对。
> 剑5–21 的导入方法见 **[docs/修复记录与剑5-21导入指南.md](docs/修复记录与剑5-21导入指南.md)**。

## 快速开始（Windows）

1. 安装 [Python 3.9+](https://www.python.org/downloads/)（安装时勾选 *Add python.exe to PATH*）。
2. 双击 **`setup.bat`**（只需一次：创建 `.venv` 并安装 pywebview）。
3. 双击 **`启动客户端(无黑框版).vbs`**，或 `run.bat`（带命令行窗口，出错时能看到原因）。

听力音频放在 `听力/` 目录（zip 或 mp3 都行），程序会自动识别并在首次播放时解压，不需要手动处理。

其他系统 / 开发调试：

```bash
pip install -r requirements.txt
python ielts_client/app.py            # 独立窗口
python ielts_client/app.py --browser  # 用浏览器打开
python ielts_client/app.py --server   # 只启动本地服务
```

## 功能

**全真模考**
- 听力：4 段录音连续播放一次，不能暂停/回放，结束后 2 分钟检查时间，自动交卷。
- 阅读：60 分钟倒计时，剩余 10/5 分钟提醒；文章划词高亮，左右分栏可拖动。
- 题号导航（已答 / 未答 / 标记复查），中途关闭可继续上次考试。
- 交卷后按剑桥换算表给出 Band 分、按题型统计、错题明细，可导出 CSV。

**日常练习**
- 每组题“核对本组答案”：显示参考答案、是否超字数；听力 ▶ 听原文，阅读“定位原文”高亮依据句。
- 精听播放器：±5 秒、拖动、0.75–1.5 倍速、AB 循环、带时间戳原文（点击句子跳转）。
- 历史成绩与薄弱题型汇总；所有记录保存在 `userdata/`，关窗不丢。

**判分规则**：忽略大小写与标点差异；支持 `/` 多答案、`(the)` 可省略、单复数、数字/日期多种写法、一题多空顺序不限、多选题；超出字数限制判错。

## 目录

```text
ielts_client/app.py      本地服务 + 窗口        tools/validate_data.py   题库校验
ielts_client/media.py    音频识别 / 准备        tools/prepare_media.py   检查音频识别
ielts_client/data/       题库（cXX/tY/）        tools/pdf_extract.py     PDF 提取 / 截图
ielts_client/web/        前端                   tools/transcribe.py      听力语音识别 + 答案定位
docs/                    修复记录与导入指南     tools/new_test.py        新建题库模板
```

## 开发检查

```bash
node tools/test_scoring.js        # 判分单元测试
python tools/validate_data.py     # 题库校验
python tools/prepare_media.py --check
```

## 版权说明

剑桥雅思真题及音频版权归 Cambridge University Press & Assessment 所有，仅供个人学习使用。建议将本仓库设为私有，不要公开分发原书 PDF 与音频。
