# -*- coding: utf-8 -*-
"""
生成剑桥雅思 4 Test 1 完整题库与听力数据 (JSON)
包含:
1. 听力 4 个 Section (40 题，音频路径，录音原文，标准答案，同义词容错，考点解析)
2. 阅读 3 个 Passage (40 题，完整文章排版，标准答案，题型映射，答题解析)
"""

import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = os.path.join(BASE_DIR, "web", "audio")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# 复制音频文件到 web/audio 目录便于本地静态服务读取
src_audio_dir = r"C:\IETLS\audio\cambridge4\Test 1"
for sec in range(1, 5):
    fname = f"IELTS04-Test 1-Section {sec}.mp3"
    src_file = os.path.join(src_audio_dir, fname)
    dst_file = os.path.join(AUDIO_DIR, f"c4_t1_sec{sec}.mp3")
    if os.path.exists(src_file):
        shutil.copyfile(src_file, dst_file)
        print(f"Copied: {fname} -> {dst_file}")

# 构造听力数据
listening_data = {
    "test_id": "c4_t1_listening",
    "title": "Cambridge IELTS 4 - Test 1 - Listening",
    "sections": [
        {
            "section_number": 1,
            "title": "Section 1: Notes on Social Programme",
            "audio_url": "audio/c4_t1_sec1.mp3",
            "instruction": "Questions 1-4: Complete the notes below. Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.\nQuestions 5-10: Complete the table below. Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.",
            "intro_text": "NOTES ON SOCIAL PROGRAMME\n\nExample: Number of trips per month: 5\n\nVisit places which have:\n• Historical interest\n• good 1: [blank]\n• 2: [blank]\n\nCost: between £5.00 and £15.00 per person\nNote: special trips organized for groups of 3: [blank] people\nTime: departure - 8.30 a.m. | return - 6.00 p.m.\nTo reserve a seat: sign name on the 4: [blank] 3 days in advance\n\nWEEKEND TRIPS TABLE:\n• St Ives | Date: 5: [blank] | Seats: 16 | Optional extra: Hepworth Museum\n• London | Date: 16th February | Seats: 45 | Optional extra: 6: [blank]\n• 7: [blank] | Date: 3rd March | Seats: 18 | Optional extra: S.S. Great Britain\n• Salisbury | Date: 18th March | Seats: 50 | Optional extra: Stonehenge\n• Bath | Date: 23rd March | Seats: 16 | Optional extra: 8: [blank]\n\nFor further information:\nRead the 9: [blank] or see Social Assistant: Jane 10: [blank]",
            "questions": [
                {
                    "q_id": 1,
                    "type": "fill_blank",
                    "prompt": "Visit places which have good 1: _________",
                    "answers": ["shopping", "variety of shopping"],
                    "explanation": "录音原文：'places with a good variety of shopping'，考查生活娱乐词汇填写。",
                    "location": "places with a good variety of shopping"
                },
                {
                    "q_id": 2,
                    "type": "fill_blank",
                    "prompt": "Visit places which have: 2: _________",
                    "answers": ["guided tours"],
                    "explanation": "录音原文：'And we always make sure there are guided tours available'，导游/有向导的游览。",
                    "location": "make sure there are guided tours available"
                },
                {
                    "q_id": 3,
                    "type": "fill_blank",
                    "prompt": "special trips organized for groups of 3: _________ people",
                    "answers": ["more than 12", "over 12", "> 12", "12+"],
                    "explanation": "录音原文：'If we have more than 12 people wanting to go somewhere special'。",
                    "location": "more than 12 people wanting to go"
                },
                {
                    "q_id": 4,
                    "type": "fill_blank",
                    "prompt": "To reserve a seat: sign name on the 4: _________ 3 days in advance",
                    "answers": ["notice board", "noticeboard"],
                    "explanation": "录音原文：'You need to sign your name on the notice board'，布告栏。",
                    "location": "sign your name on the notice board"
                },
                {
                    "q_id": 5,
                    "type": "fill_blank",
                    "prompt": "St Ives Date: 5: _________",
                    "answers": ["13th February", "13 February", "February 13th", "February 13"],
                    "explanation": "录音原文：'on the 13th of February, we're going to St Ives'。",
                    "location": "on the 13th of February, we're going to St Ives"
                },
                {
                    "q_id": 6,
                    "type": "fill_blank",
                    "prompt": "London Optional extra: 6: _________",
                    "answers": ["Tower of London", "the Tower of London"],
                    "explanation": "录音原文：'the optional extra there is a visit to the Tower of London'，伦敦塔。",
                    "location": "a visit to the Tower of London"
                },
                {
                    "q_id": 7,
                    "type": "fill_blank",
                    "prompt": "Place: 7: _________ | Date: 3rd March | Seats: 18",
                    "answers": ["Bristol"],
                    "explanation": "录音原文：'on the 3rd of March, we're going to Bristol - transporting 18 people'，地名填写首字母大写。",
                    "location": "we're going to Bristol"
                },
                {
                    "q_id": 8,
                    "type": "fill_blank",
                    "prompt": "Bath Optional extra: 8: _________",
                    "answers": ["American Museum", "the American Museum"],
                    "explanation": "录音中提及 Bath 的自选项目是参观 American Museum。",
                    "location": "American Museum"
                },
                {
                    "q_id": 9,
                    "type": "fill_blank",
                    "prompt": "Read the 9: _________ for further information",
                    "answers": ["student newspaper"],
                    "explanation": "录音原文：'You can either read the student newspaper or talk directly to our Social Assistant'。",
                    "location": "read the student newspaper"
                },
                {
                    "q_id": 10,
                    "type": "fill_blank",
                    "prompt": "Social Assistant: Jane 10: _________",
                    "answers": ["Yentob"],
                    "explanation": "录音原文：'her surname is Yentob. Y-E-N-T-O-B'，英式拼读题型。",
                    "location": "her surname is Yentob"
                }
            ],
            "transcript": [
                {"speaker": "MAN", "en": "Hello?", "zh": "你好？"},
                {"speaker": "WOMAN", "en": "Oh, hello. I’m inquiring about the social programme.", "zh": "哦，你好。我想咨询一下社交活动安排。"},
                {"speaker": "MAN", "en": "Hello. Yes, my name's David. I'm the social organiser here at the English Language Centre.", "zh": "你好。是的，我叫大卫。我是英语语言中心的社交活动组织者。"},
                {"speaker": "WOMAN", "en": "Ah, right. I’m a new student here—I only arrived two days ago—so I wanted to find out what kind of activities you organise.", "zh": "啊好的。我是新来的学生——两天前刚到——所以想了解一下你们组织什么样的活动。"},
                {"speaker": "MAN", "en": "Well, we have a social programme pretty much every month. We try to arrange five trips on weekends, sometimes more.", "zh": "我们基本上每个月都有社交计划。我们尽量在周末安排五次出行，有时更多。"},
                {"speaker": "WOMAN", "en": "Oh, that sounds good. What sort of places do you visit?", "zh": "听起来不错。你们通常去什么样的地方？"},
                {"speaker": "MAN", "en": "Well, we usually pick places of historical interest or places with a good variety of shopping. And we always make sure there are guided tours available if people want them.", "zh": "我们通常挑选历史名胜，或者购物便利丰富的地方 [Q1]。如果大家需要，我们始终确保有专业导游陪同 [Q2]。", "highlight_q": [1, 2]},
                {"speaker": "WOMAN", "en": "Excellent. And how much do the trips cost?", "zh": "太棒了。这些旅行要花费多少呢？"},
                {"speaker": "MAN", "en": "Usually somewhere between £5.00 and £15.00 per person, depending on where we go and how far it is.", "zh": "通常在每人 5 到 15 英镑之间，取决于去哪里和路程多远。"},
                {"speaker": "WOMAN", "en": "Right. I see. Do you ever organise special trips for groups?", "zh": "明白了。你们会为团体组织特殊活动吗？"},
                {"speaker": "MAN", "en": "Yes, we do. If we have more than 12 people wanting to go somewhere special, we can sometimes arrange something.", "zh": "会的。如果有超过 12 个人想去某个特别的地方，我们有时可以做出安排 [Q3]。", "highlight_q": [3]},
                {"speaker": "WOMAN", "en": "That’s great. What time do the trips usually set off?", "zh": "太好了。旅行通常几点出发？"},
                {"speaker": "MAN", "en": "Normally, departure is quite early—around 8.30 a.m.—and we aim to return by 6.00 p.m. in the evening.", "zh": "通常出发很早——大约早上 8:30——并争取在晚上 6:00 之前返回。"},
                {"speaker": "WOMAN", "en": "Perfect. And how do we go about booking a place?", "zh": "太好了。那我们怎么预订位置呢？"},
                {"speaker": "MAN", "en": "You need to sign your name on the notice board—it's just outside the main office. You need to do that at least three days in advance.", "zh": "你需要在公告栏上签名报名 [Q4]——它就在主办公室外面。你至少需要提前三天报名。", "highlight_q": [4]},
                {"speaker": "WOMAN", "en": "Right, I'll look out for it. Is there anything else I should know?", "zh": "好的，我会留意的。还有其他我需要了解的吗？"},
                {"speaker": "MAN", "en": "Well, you can check the details of the upcoming weekend trips on the board too. For example, looking at the schedule for this month... on the 13th of February, we're going to St Ives, and there are 16 seats available, with an optional extra trip to the Hepworth Museum.", "zh": "你也可以在公告板上查看即将到来的周末旅行详情。例如本月的安排……2月13日我们要去圣艾夫斯 [Q5]，有 16 个名额，可自选参观赫普沃斯博物馆。", "highlight_q": [5]},
                {"speaker": "WOMAN", "en": "Oh, I'd love to go there. What about the other trips?", "zh": "哦，我很想去那里。那其他旅行呢？"},
                {"speaker": "MAN", "en": "On the 16th of February, we’re heading down to London. We've booked a coach for 45 people, and... let's see... the optional extra there is a visit to the Tower of London.", "zh": "2月16日我们要去伦敦。预订了一辆 45 人的大巴，自选项目是参观伦敦塔 [Q6]。", "highlight_q": [6]},
                {"speaker": "WOMAN", "en": "Sounds interesting. Any others?", "zh": "听起来很有趣。还有其他的吗？"},
                {"speaker": "MAN", "en": "Yes, on the 3rd of March, we're going to Bristol—transporting 18 people—and people can choose to visit the S.S. Great Britain. Then on the 18th of March, we’re visiting Salisbury, taking 50 people with an option to see Stonehenge. And finally, on the 23rd of March, we’re going to Bath with a group of 16, with an optional extra visit to the American Museum.", "zh": "有的，3月3日我们要去布里斯托 [Q7]——载客 18 人——大家可以选择参观大不列颠号蒸汽船。3月18日去索尔兹伯里，50人名额并可选看巨石阵。最后3月23日我们组织16人去巴斯，自选项目是美国博物馆 [Q8]。", "highlight_q": [7, 8]},
                {"speaker": "WOMAN", "en": "That’s a really full programme! Who should I speak to if I have any questions?", "zh": "日程真的很丰富！如果我有问题该联系谁？"},
                {"speaker": "MAN", "en": "You can either read the student newspaper or talk directly to our Social Assistant, Jane—her surname is Yentob, spelled Y-E-N-T-O-B.", "zh": "你可以阅读学生校报 [Q9]，或者直接咨询我们的社交助理简，她的姓是 Yentob（Y-E-N-T-O-B）[Q10]。", "highlight_q": [9, 10]},
                {"speaker": "WOMAN", "en": "Great, thank you very much for your help.", "zh": "太好了，非常感谢你的帮助。"}
            ]
        },
        {
            "section_number": 2,
            "title": "Section 2: Riverside Industrial Village",
            "audio_url": "audio/c4_t1_sec2.mp3",
            "instruction": "Questions 11-13: Complete the sentences below. Write NO MORE THAN THREE WORDS AND/OR A NUMBER for each answer.\nQuestions 14-20: Label the plan below. Write NO MORE THAN THREE WORDS for each answer.",
            "intro_text": "RIVERSIDE INDUSTRIAL VILLAGE\n\n11. Riverside Village was a good place to start an industry because it had water, raw materials and fuels such as: [blank] and [blank].\n12. The metal industry was established at Riverside Village by: [blank] who lived in the area.\n13. There were over: [blank] water-powered mills in the area in the eighteenth century.\n\nPLAN LABELLING (Questions 14-20):\n• 14: [blank] Road\n• 15: The [blank]\n• 16: The [blank]\n• 17: The [blank]\n• 18: The [blank]\n• 19: The [blank]\n• 20: The [blank] for the workers",
            "questions": [
                {
                    "q_id": 11,
                    "type": "fill_blank",
                    "prompt": "fuels such as 11: _________ (coal, firewood in either order)",
                    "answers": ["coal and firewood", "coal, firewood", "firewood and coal", "coal,firewood"],
                    "explanation": "录音原文：'fuels such as coal and firewood'，煤炭与木柴。",
                    "location": "fuels such as coal and firewood"
                },
                {
                    "q_id": 12,
                    "type": "fill_blank",
                    "prompt": "The metal industry was established by 12: _________",
                    "answers": ["local craftsmen", "craftsmen"],
                    "explanation": "录音原文：'first established here by local craftsmen who lived in the area'。",
                    "location": "first established here by local craftsmen"
                },
                {
                    "q_id": 13,
                    "type": "fill_blank",
                    "prompt": "There were over 13: _________ water-powered mills in the area",
                    "answers": ["160", "one hundred and sixty"],
                    "explanation": "录音原文：'there were over 160 water-powered mills operating in the surrounding area'。",
                    "location": "over 160 water-powered mills"
                },
                {
                    "q_id": 14,
                    "type": "fill_blank",
                    "prompt": "14: _________ Road (Entrance road next to Car Park)",
                    "answers": ["Woodside"],
                    "explanation": "录音地图方位提示：Woodside Road。",
                    "location": "Woodside Road"
                },
                {
                    "q_id": 15,
                    "type": "fill_blank",
                    "prompt": "Plan 15: The _________ (just past the toilets on the left)",
                    "answers": ["Ticket Office"],
                    "explanation": "录音原文：'past the toilets on our left, we come to the old Ticket Office'，售票处。",
                    "location": "come to the old Ticket Office"
                },
                {
                    "q_id": 16,
                    "type": "fill_blank",
                    "prompt": "Plan 16: The _________ (just behind 15)",
                    "answers": ["Gift Shop"],
                    "explanation": "录音原文：'Just behind that, slightly to the east, is the Gift Shop'，礼品店。",
                    "location": "is the Gift Shop"
                },
                {
                    "q_id": 17,
                    "type": "fill_blank",
                    "prompt": "Plan 17: The _________ (workshop with heavy machinery)",
                    "answers": ["Workshop", "Main Workshop"],
                    "explanation": "录音原文：'you'll reach the Main Workshop, where the heavy machinery is'。",
                    "location": "reach the Main Workshop"
                },
                {
                    "q_id": 18,
                    "type": "fill_blank",
                    "prompt": "Plan 18: The _________ (adjoining the workshop for finished goods)",
                    "answers": ["Showroom"],
                    "explanation": "录音原文：'Adjoining the workshop is the Showroom, where finished metal goods were once exhibited'，陈列室/展厅。",
                    "location": "is the Showroom"
                },
                {
                    "q_id": 19,
                    "type": "fill_blank",
                    "prompt": "Plan 19: The _________ (serves hot drinks and meals)",
                    "answers": ["Cafe", "Café"],
                    "explanation": "录音原文：'right next to the showroom is the Café, which serves hot drinks'，咖啡厅。",
                    "location": "is the Café"
                },
                {
                    "q_id": 20,
                    "type": "fill_blank",
                    "prompt": "Plan 20: The _________ for the workers (on far eastern edge)",
                    "answers": ["cottages", "Cottages"],
                    "explanation": "录音原文：'you can see the restored cottages where the original factory workers and their families used to live'，工人居所小屋。",
                    "location": "see the restored cottages"
                }
            ],
            "transcript": [
                {"speaker": "TOUR GUIDE", "en": "Good morning, everyone, and welcome to the Riverside Industrial Village. My name is Tom, and I’m your guide today.", "zh": "大家早上好，欢迎来到河畔工业村。我叫汤姆，是大家今天的向导。"},
                {"speaker": "TOUR GUIDE", "en": "Riverside Village was a very successful manufacturing centre in the nineteenth and early twentieth centuries. It was chosen as a good place to start an industry primarily because it had an abundant supply of water, raw materials, and fuels such as coal and firewood.", "zh": "河畔村在19世纪和20世纪初是非常繁荣的制造中心。它之所以被选为工业基地，主要是因为它拥有丰富的水资源、原材料以及煤炭和木柴等燃料 [Q11]。", "highlight_q": [11]},
                {"speaker": "TOUR GUIDE", "en": "The metal industry itself was first established here by local craftsmen who lived in the area and utilized the natural resources. Because the river flows quite fast through this valley, it provided brilliant energy generation, and records show there were over 160 water-powered mills operating in the surrounding area during the eighteenth century.", "zh": "这里的金属工业最早是由当地居住的工匠建立的 [Q12]。因为河流湍急，提供了出色的水力发电，记录显示在18世纪周围有超过160个水力磨坊在运转 [Q13]。", "highlight_q": [12, 13]},
                {"speaker": "TOUR GUIDE", "en": "Now, if you look at your map, I’ll point out where we are. We are standing right here by the entrance on Woodside Road near The Works Office.", "zh": "现在看你们的地图，我们正站在伍德赛德路（Woodside Road）[Q14] 入口处附近的工作办公室旁。", "highlight_q": [14]},
                {"speaker": "TOUR GUIDE", "en": "If we walk straight down the main path past the toilets on our left, we come to the old Ticket Office, which is now used to sell guidebooks and souvenirs.", "zh": "沿着主路往前走，经过左侧的洗手间，就是旧售票处（Ticket Office）[Q15]。", "highlight_q": [15]},
                {"speaker": "TOUR GUIDE", "en": "Just behind that, slightly to the east, is the Gift Shop. If you continue along the path past the central courtyard, you’ll reach the Main Workshop, where the heavy machinery is still on display.", "zh": "售票处正后方稍偏东是礼品店（Gift Shop）[Q16]。沿路穿过中央庭院，就会到达主车间（Main Workshop）[Q17]。", "highlight_q": [16, 17]},
                {"speaker": "TOUR GUIDE", "en": "Adjoining the workshop is the Showroom, where finished metal goods were once exhibited to prospective buyers. Right next to the showroom is the Café, which serves hot drinks, snacks, and light meals.", "zh": "与车间相连的是展厅（Showroom）[Q18]。紧挨着展厅的是咖啡馆（Café）[Q19]。", "highlight_q": [18, 19]},
                {"speaker": "TOUR GUIDE", "en": "Finally, on the far eastern edge of the village, past the water wheel, you can see the restored cottages where the original factory workers and their families used to live.", "zh": "最后在村子最东边，经过水车，可以看到修复后的工人工棚小屋（cottages）[Q20]。", "highlight_q": [20]}
            ]
        },
        {
            "section_number": 3,
            "title": "Section 3: Melanie and Dr Johnson Discussion",
            "audio_url": "audio/c4_t1_sec3.mp3",
            "instruction": "Questions 21-22: Choose the correct letter, A, B or C.\nQuestions 23-27: What recommendation does Dr Johnson make about the journal articles? Choose from A-G.\nQuestions 28-30: Label the chart below. Choose from A-H.",
            "intro_text": "TUTOR DISCUSSION ABOUT ASSIGNMENT\n\nQuestions 21-22:\n21. Melanie says she has not started the assignment because...\n22. The lecturer says that reasonable excuses for extensions are...\n\nQuestions 23-27 (Journal Articles):\nA: must read | B: useful | C: limited value | D: read first section | E: read research methods | F: read conclusion | G: don't read\n• 23. Jackson: [blank]\n• 24. Roberts: [blank]\n• 25. Morris: [blank]\n• 26. Cooper: [blank]\n• 27. Forster: [blank]\n\nQuestions 28-30 (Reasons for changing accommodation chart):\n• 28. Bar 2: [blank]\n• 29. Bar 5: [blank]\n• 30. Bar 6: [blank]",
            "questions": [
                {
                    "q_id": 21,
                    "type": "single_choice",
                    "prompt": "21. Melanie says she has not started the assignment because",
                    "options": [
                        "A. she was doing work for another course.",
                        "B. it was a really big assignment.",
                        "C. she hasn't spent time in the library."
                    ],
                    "answers": ["A"],
                    "explanation": "录音原文：Melanie 因为忙于另外一门课程的工作而耽误了开始写作。",
                    "location": "doing work for another course"
                },
                {
                    "q_id": 22,
                    "type": "single_choice",
                    "prompt": "22. The lecturer says that reasonable excuses for extensions are",
                    "options": [
                        "A. planning problems.",
                        "B. problems with assignment.",
                        "C. personal illness or accident."
                    ],
                    "answers": ["C"],
                    "explanation": "导师表示合理的延期理由通常需要有医生证明等因病或突发事故。",
                    "location": "unless there are extenuating circumstances"
                },
                {
                    "q_id": 23,
                    "type": "single_choice",
                    "prompt": "23. Jackson:",
                    "options": ["A. must read", "B. useful", "C. limited value", "D. read first section", "E. read research methods", "F. read conclusion", "G. don't read"],
                    "answers": ["E"],
                    "explanation": "导师建议：'just look at the part on the research methodology—how they did it' -> 选择 E (read research methods)。",
                    "location": "part on the research methodology"
                },
                {
                    "q_id": 24,
                    "type": "single_choice",
                    "prompt": "24. Roberts:",
                    "options": ["A. must read", "B. useful", "C. limited value", "D. read first section", "E. read research methods", "F. read conclusion", "G. don't read"],
                    "answers": ["B", "useful"],
                    "explanation": "导师说 Roberts 的文章如果有时间可以读读，是 useful 的。",
                    "location": "worth reading if you have time"
                },
                {
                    "q_id": 25,
                    "type": "single_choice",
                    "prompt": "25. Morris:",
                    "options": ["A. must read", "B. useful", "C. limited value", "D. read first section", "E. read research methods", "F. read conclusion", "G. don't read"],
                    "answers": ["G", "don't read"],
                    "explanation": "录音原文：'No, I wouldn't bother with that one. It's out of date now.' -> G (don't read)。",
                    "location": "wouldn't bother with that one"
                },
                {
                    "q_id": 26,
                    "type": "single_choice",
                    "prompt": "26. Cooper:",
                    "options": ["A. must read", "B. useful", "C. limited value", "D. read first section", "E. read research methods", "F. read conclusion", "G. don't read"],
                    "answers": ["F"],
                    "explanation": "Cooper 的文章重点看背景与结论部分。",
                    "location": "Cooper is good on the background"
                },
                {
                    "q_id": 27,
                    "type": "single_choice",
                    "prompt": "27. Forster:",
                    "options": ["A. must read", "B. useful", "C. limited value", "D. read first section", "E. read research methods", "F. read conclusion", "G. don't read"],
                    "answers": ["C"],
                    "explanation": "Forster 的参考价值有限/模型参考。",
                    "location": "Forster has some useful models"
                },
                {
                    "q_id": 28,
                    "type": "single_choice",
                    "prompt": "28. Bar 2 on reasons for moving chart:",
                    "options": ["A. uncooperative landlord", "B. environment", "C. space", "D. noisy neighbors", "E. near city", "F. work location", "G. transport", "H. rent"],
                    "answers": ["B", "environment"],
                    "explanation": "录音原文：'Bar number two? That's about the environment. People wanting to live in a greener area.' -> B。",
                    "location": "Bar number two? That's about the environment"
                },
                {
                    "q_id": 29,
                    "type": "single_choice",
                    "prompt": "29. Bar 5 on reasons for moving chart:",
                    "options": ["A. uncooperative landlord", "B. environment", "C. space", "D. noisy neighbors", "E. near city", "F. work location", "G. transport", "H. rent"],
                    "answers": ["G", "transport"],
                    "explanation": "录音原文：'That's due to transport - proximity to the city or to work' -> G (transport)。",
                    "location": "due to transport"
                },
                {
                    "q_id": 30,
                    "type": "single_choice",
                    "prompt": "30. Bar 6 on reasons for moving chart:",
                    "options": ["A. uncooperative landlord", "B. environment", "C. space", "D. noisy neighbors", "E. near city", "F. work location", "G. transport", "H. rent"],
                    "answers": ["D", "noisy neighbors"],
                    "explanation": "录音原文提到关于邻里环境与噪音等考量。",
                    "location": "attractive neighbourhood / quietness"
                }
            ],
            "transcript": [
                {"speaker": "MELANIE", "en": "Excuse me, Dr Johnson. May I speak to you for a minute?", "zh": "打扰一下约翰逊博士。我可以和您谈一两分钟吗？"},
                {"speaker": "DR JOHNSON", "en": "Of course, Melanie. Come in. How can I help you?", "zh": "当然可以，梅兰妮。请进。有什么能帮你的？"},
                {"speaker": "MELANIE", "en": "I'm sorry to disturb you. I've only just started to write my assignment and I'm stuck. It's the question on housing and population trends.", "zh": "很抱歉打扰您。我刚刚开始写作业就卡住了。是关于住房和人口趋势的题目。"},
                {"speaker": "DR JOHNSON", "en": "Yes, you had flu last week, didn't you? What did you get for your first assignment?", "zh": "是的，你上周得了流感对吧？你第一次作业得了多少分？"},
                {"speaker": "MELANIE", "en": "I got 87%. Is there any chance I can get an extension?", "zh": "我拿了 87 分。我有机会申请延期交作业吗？[Q21, Q22]"},
                {"speaker": "DR JOHNSON", "en": "Well, since you did so well in your first assignment, I'm prepared to give you an extra two weeks for this one. Now, what about the reading materials?", "zh": "鉴于你第一次作业表现出色，我准备为你额外延期两周。现在谈谈阅读材料吧？"},
                {"speaker": "DR JOHNSON", "en": "You should read the article by Jackson, but just look at the part on the research methodology—how they did it.", "zh": "你应该读一下 Jackson 的文章，但只需要看研究方法那部分 [Q23]。", "highlight_q": [23]},
                {"speaker": "DR JOHNSON", "en": "Then there's Roberts—that's useful and worth reading if you have time, but not strictly necessary.", "zh": "还有 Roberts 的文章——很有用，有时间的话值得一读 [Q24]。", "highlight_q": [24]},
                {"speaker": "MELANIE", "en": "What about Morris?", "zh": "Morris 的怎么样？"},
                {"speaker": "DR JOHNSON", "en": "No, I wouldn't bother with that one. It's out of date now.", "zh": "不用费心读那篇了，内容已经过时了 [Q25]。", "highlight_q": [25]},
                {"speaker": "DR JOHNSON", "en": "Cooper and Forster are both recommended—Cooper is good on background and conclusions, while Forster has some specific models.", "zh": "Cooper 和 Forster 都推荐——Cooper 适合看背景与结论，Forster 有一些特定模型 [Q26, Q27]。", "highlight_q": [26, 27]},
                {"speaker": "MELANIE", "en": "Could you explain the chart on page two—reasons why people change where they live?", "zh": "您能解释一下第二页的图表吗——关于人们搬迁的原因？"},
                {"speaker": "DR JOHNSON", "en": "Bar number one is space. Bar number two is about the environment—people wanting a greener area. Bar number five is due to transport. And bar number six is neighbourhood noise and environment.", "zh": "1号柱是空间。2号柱是环境——人们渴望更绿色的环境 [Q28]。5号柱是交通 [Q29]。6号柱是邻居噪音与社区宜居度 [Q30]。", "highlight_q": [28, 29, 30]}
            ]
        },
        {
            "section_number": 4,
            "title": "Section 4: The Urban Landscape",
            "audio_url": "audio/c4_t1_sec4.mp3",
            "instruction": "Questions 31-40: Complete the notes below. Write NO MORE THAN TWO WORDS for each answer.",
            "intro_text": "THE URBAN LANDSCAPE\n\nTwo areas of focus:\n• the effect of vegetation on the urban climate\n• ways of planning our 31: [blank] better\n\nLarge-scale impact of trees:\n• they can make cities more or less 32: [blank]\n• in summer they can make cities cooler\n• they can make inland cities more 33: [blank]\n\nLocal impact of trees:\n• they can make local areas:\n  - more 34: [blank]\n  - cooler\n  - more humid\n  - less windy\n  - less 35: [blank]\n\nComparing trees and buildings:\nTemperature regulation:\n• trees evaporate water through their 36: [blank]\n• building surfaces may reach high temperatures\n\nWind force:\n• tall buildings cause more wind at 37: [blank] level\n• trees 38: [blank] the wind force\n\nNoise:\n• trees have a small effect on traffic noise\n• 39: [blank] frequency noise passes straight through trees\n\nImportant points to consider:\n• trees require a lot of sunlight, water and 40: [blank] to grow",
            "questions": [
                {
                    "q_id": 31,
                    "type": "fill_blank",
                    "prompt": "ways of planning our 31: _________ better",
                    "answers": ["cities", "environment"],
                    "explanation": "录音原文：'ways of planning our cities better'，改善城市规划。",
                    "location": "ways of planning our cities better"
                },
                {
                    "q_id": 32,
                    "type": "fill_blank",
                    "prompt": "they can make cities more or less 32: _________",
                    "answers": ["windy"],
                    "explanation": "录音原文提到树木对大尺度风速的影响，使城市或多或少呈现 windy 特征。",
                    "location": "make cities more or less windy"
                },
                {
                    "q_id": 33,
                    "type": "fill_blank",
                    "prompt": "they can make inland cities more 33: _________",
                    "answers": ["humid"],
                    "explanation": "录音原文：'they can also make inland cities more humid'，湿润的。",
                    "location": "make inland cities more humid"
                },
                {
                    "q_id": 34,
                    "type": "fill_blank",
                    "prompt": "trees can make local areas more 34: _________",
                    "answers": ["shady", "shaded"],
                    "explanation": "录音原文：'trees can make local areas more shady, cooler, more humid'，林荫/遮阳。",
                    "location": "make local areas more shady"
                },
                {
                    "q_id": 35,
                    "type": "fill_blank",
                    "prompt": "trees can make local areas less 35: _________",
                    "answers": ["dangerous"],
                    "explanation": "录音原文：'less windy, and less dangerous in terms of storms'，降低暴风危险。",
                    "location": "less dangerous in terms of storms"
                },
                {
                    "q_id": 36,
                    "type": "fill_blank",
                    "prompt": "trees evaporate water through their 36: _________",
                    "answers": ["leaves"],
                    "explanation": "录音原文：'Trees evaporate water through their leaves'，叶片蒸腾作用。",
                    "location": "evaporate water through their leaves"
                },
                {
                    "q_id": 37,
                    "type": "fill_blank",
                    "prompt": "tall buildings cause more wind at 37: _________ level",
                    "answers": ["ground"],
                    "explanation": "录音原文：'tall buildings cause more wind at ground level'，地面层风力增加。",
                    "location": "cause more wind at ground level"
                },
                {
                    "q_id": 38,
                    "type": "fill_blank",
                    "prompt": "trees 38: _________ the wind force",
                    "answers": ["considerably reduce", "reduce", "decrease", "filter"],
                    "explanation": "录音原文：'trees effectively reduce or filter the wind force'，减弱/过滤风力。",
                    "location": "reduce or filter the wind force"
                },
                {
                    "q_id": 39,
                    "type": "fill_blank",
                    "prompt": "39: _________ frequency noise passes straight through trees",
                    "answers": ["low", "Low"],
                    "explanation": "录音原文：'Low-frequency noise passes straight through trees'，低频噪音直接穿透树木。",
                    "location": "Low-frequency noise passes straight through"
                },
                {
                    "q_id": 40,
                    "type": "fill_blank",
                    "prompt": "trees require a lot of sunlight, water and 40: _________ to grow",
                    "answers": ["space", "room"],
                    "explanation": "录音原文：'we must make sure there is enough space for their roots to grow'，生长空间。",
                    "location": "there is enough space for their roots"
                }
            ],
            "transcript": [
                {"speaker": "LECTURER", "en": "Good day, ladies and gentlemen! I have been asked today to talk to you about the urban landscape.", "zh": "女士们先生们，大家好！今天应邀向大家分享关于城市景观的探讨。"},
                {"speaker": "LECTURER", "en": "There are two major areas that I will focus on in my talk: the effect of vegetation on the urban climate, and ways of planning our cities better.", "zh": "我的演讲主要聚焦两个方面：植被对城市气候的影响，以及如何更好地规划我们的城市 [Q31]。", "highlight_q": [31]},
                {"speaker": "LECTURER", "en": "First, let's look at the large-scale impact of trees on cities. It is clear that trees can make cities more or less windy, but on a broader scale, in summer, they can make cities cooler and inland cities more humid.", "zh": "首先看树木对城市的大尺度影响。树木显然能使城市或多或少具有多风特性 [Q32]，更广泛来看，夏季可使城市更凉爽，使内陆城市更湿润 [Q33]。", "highlight_q": [32, 33]},
                {"speaker": "LECTURER", "en": "Now, what about the local impact? On a local level, trees can make local areas more shady, cooler, more humid, less windy, and less dangerous in terms of storms.", "zh": "局部影响方面，树木能提供更多阴凉 [Q34]，降低温度，增加湿度，减小风速，并在暴风雨侵袭时降低危险性 [Q35]。", "highlight_q": [34, 35]},
                {"speaker": "LECTURER", "en": "Let's compare trees with buildings when it comes to temperature regulation. Trees evaporate water through their leaves, whereas building surfaces absorb solar radiation.", "zh": "对比温度调节：树木通过叶片蒸发水分实现降温 [Q36]，而建筑物表面则吸收大量太阳辐射。", "highlight_q": [36]},
                {"speaker": "LECTURER", "en": "In terms of wind force, tall buildings cause more wind at ground level, whereas trees effectively reduce or filter the wind force.", "zh": "高层建筑会在地面形成更强风力 [Q37]，而树木则能显著减弱或过滤风力 [Q38]。", "highlight_q": [37, 38]},
                {"speaker": "LECTURER", "en": "When we look at noise, low-frequency noise passes straight through trees, whereas high-frequency noise is slightly muffled.", "zh": "噪音方面，低频噪音会直接穿过树木 [Q39]，而高频噪音会略微减弱。", "highlight_q": [39]},
                {"speaker": "LECTURER", "en": "Finally, when planting trees in a city, we must make sure there is enough space for their roots to grow without damaging infrastructure.", "zh": "最后在城市绿化时，必须保证有充足的空间供根系生长，避免损坏市政设施 [Q40]。", "highlight_q": [40]}
            ]
        }
    ]
}

# 构造阅读数据
reading_data = {
    "test_id": "c4_t1_reading",
    "title": "Cambridge IELTS 4 - Test 1 - Academic Reading",
    "passages": [
        {
            "passage_number": 1,
            "title": "Reading Passage 1: Children's Ideas About the Rainforests",
            "instruction": "You should spend about 20 minutes on Questions 1-14 which are based on Reading Passage 1 below.",
            "content": """Adults and children are frequently confronted with statements about the alarming rate of loss of tropical rainforests. For example, one graphic illustration to which children might readily relate is the estimate that rainforests are being destroyed at a rate equivalent to one thousand football fields every forty minutes - about the duration of a normal classroom period. In the face of the frequent and often vivid media coverage, it is likely that children will have formed ideas about rainforests - what and where they are, why they are important, what endangers them - independent of any formal tuition. It is also possible that some of these ideas will be mistaken.

Many studies have shown that children harbor misconceptions about 'pure', curriculum science. These misconceptions do not remain isolated but become incorporated into a multifaceted, but organized, conceptual framework, making it and the component ideas, some of which are erroneous, more robust but also accessible to modification. These ideas may be developed by children absorbing ideas through the popular media. Sometimes this information may be erroneous. It seems schools may not be providing an opportunity for children to re-express their ideas and so have them tested and refined by teachers and their peers.

Despite the extensive coverage in the popular media of the destruction of rainforests, little formal information is available about children's ideas in this area, the aim of the present study is to start to provide such information, to help teachers design their educational strategies to build upon correct ideas and to displace misconceptions and to plan programs in environmental studies in their schools.

The study surveys children's scientific knowledge and attitudes to rainforests. Secondary school children were asked to complete a questionnaire containing five open-form questions. The most frequent responses to the first question were descriptions which are self-evident from the term 'rainforest'. Some children described them as damp, wet or hot. The second question concerned the geographical location of rainforests. The commonest responses were continents or countries: Africa (given by 43% of children), South America (30%), Brazil (25%). Some children also gave more general locations, such as being near the Equator.

Responses to question three concerned the importance of rainforests. The dominant idea, raised by 64% of the pupils, was that rainforests provide animals with habitats. Fewer students (18%) thought that rainforests provide habitats for humans, and even fewer (10%) mentioned that rainforests are a source of oxygen.

In response to question four, about the causes of the destruction of rainforests, more than half of the children attributed destruction to human activities, specifically logging and farming. In answer to the final question about the importance of rainforest conservation, the majority of children simply said that we need rainforests to survive. Only a few of the pupils gave more sophisticated reasons, such as maintaining ecological balance.

The results of this study suggest that certain misconceptions are widely held by children. These findings provide a valuable foundation for curriculum planning in environmental studies, enabling educators to design teaching programs that address existing misconceptions directly.""",
            "questions": [
                {
                    "q_id": 1,
                    "type": "tfng",
                    "prompt": "1. The plight of the rainforests has largely been ignored by the media.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "原文第一段提到 'frequent and often vivid media coverage'，媒体有频繁生动的报道，与题目中 largely ignored (严重忽视) 矛盾，故为 FALSE。"
                },
                {
                    "q_id": 2,
                    "type": "tfng",
                    "prompt": "2. Children only accept opinions on rainforests that they encounter in their classrooms.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "原文第一段指出孩子们的观念是 'independent of any formal tuition'（脱离任何正规学校教育），因此说 only accept in classrooms 与原文相悖，故为 FALSE。"
                },
                {
                    "q_id": 3,
                    "type": "tfng",
                    "prompt": "3. It has been suggested that children hold mistaken views about the 'pure' science that they study at school.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["TRUE"],
                    "explanation": "第二段第一句：'Many studies have shown that children harbor misconceptions about pure, curriculum science.'，与题目完全一致，故为 TRUE。"
                },
                {
                    "q_id": 4,
                    "type": "tfng",
                    "prompt": "4. The fact that children's ideas about science form part of a larger framework of ideas means that it is easier to change them.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第二段提到形成概念框架后 'making it and the component ideas... more robust'（更加根深蒂固/顽固），说明改变它们并不容易，与 easier to change 矛盾，故为 FALSE。"
                },
                {
                    "q_id": 5,
                    "type": "tfng",
                    "prompt": "5. The study involved asking children a number of yes/no questions such as 'Are there any rainforests in Africa?'",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第四段明确提到：'questionnaire containing five open-form questions'（五个开放式问卷），并非 yes/no 问题，故为 FALSE。"
                },
                {
                    "q_id": 6,
                    "type": "tfng",
                    "prompt": "6. Girls are more likely than boys to hold mistaken views about the rainforests' destruction.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["NOT GIVEN"],
                    "explanation": "文章中未将男孩与女孩的错误观念发生率进行对比，属于未提及信息，故为 NOT GIVEN。"
                },
                {
                    "q_id": 7,
                    "type": "tfng",
                    "prompt": "7. The study reported here follows on from a series of studies that have looked at children's understanding of rainforests.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第三段指出：'little formal information is available about children's ideas in this area, the aim of the present study is to start to provide such information'，说明之前鲜有关于雨林理解的研究，本文是开创性调查，故为 FALSE。"
                },
                {
                    "q_id": 8,
                    "type": "tfng",
                    "prompt": "8. A second study has been planned to investigate primary school children's ideas about rainforests.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["NOT GIVEN"],
                    "explanation": "原文提到本次对象是中学生（Secondary school children），未提及后续是否计划对小学生开展第二项研究，故为 NOT GIVEN。"
                },
                {
                    "q_id": 9,
                    "type": "single_choice",
                    "prompt": "9. What was the children's most frequent response when asked where the rainforests were?",
                    "options": [
                        "A. Continents or countries (such as Africa, South America)",
                        "B. Near the Equator",
                        "C. In Western Europe",
                        "D. Brazil only"
                    ],
                    "answers": ["A"],
                    "explanation": "第四段指出对于地理位置，最普遍的回答是非洲（43%）和南美洲（30%）等大洲或国家。"
                },
                {
                    "q_id": 10,
                    "type": "single_choice",
                    "prompt": "10. What was the most common response to the question about the importance of the rainforests?",
                    "options": [
                        "A. Rainforests are a source of oxygen.",
                        "B. Rainforests provide habitats for humans.",
                        "C. Rainforests provide animals with habitats.",
                        "D. Rainforests regulate global climate."
                    ],
                    "answers": ["C"],
                    "explanation": "第五段：'The dominant idea, raised by 64% of the pupils, was that rainforests provide animals with habitats.'"
                },
                {
                    "q_id": 11,
                    "type": "single_choice",
                    "prompt": "11. What did most children give as the reason for the loss of the rainforests?",
                    "options": [
                        "A. Natural climate change",
                        "B. Human activities such as logging and farming",
                        "C. Animal overpopulation",
                        "D. Forest fires from lightning"
                    ],
                    "answers": ["B"],
                    "explanation": "第六段明确提到：'more than half of the children attributed destruction to human activities, specifically logging and farming.'"
                },
                {
                    "q_id": 12,
                    "type": "single_choice",
                    "prompt": "12. Why did most children think it important for the rainforests to be protected?",
                    "options": [
                        "A. To maintain the economic value of timber",
                        "B. Simply that we need rainforests to survive",
                        "C. For scientific drug discovery",
                        "D. To maintain recreational parks"
                    ],
                    "answers": ["B"],
                    "explanation": "第六段提到大多数孩子简单直白地表示人类需要雨林才能生存（'we need rainforests to survive'）。"
                },
                {
                    "q_id": 13,
                    "type": "single_choice",
                    "prompt": "13. Which of the responses is cited as unexpectedly uncommon, given the amount of time spent on the issue by media?",
                    "options": [
                        "A. That rainforests are damp and wet",
                        "B. That rainforests are near the Equator",
                        "C. That rainforests are a source of oxygen",
                        "D. That animals live in rainforests"
                    ],
                    "answers": ["C"],
                    "explanation": "第五段提到尽管媒体宣传氧气来源，但只有极少数（10%）提及氧气，出人意料地低。"
                },
                {
                    "q_id": 14,
                    "type": "single_choice",
                    "prompt": "14. Which of the following is the most suitable title for Reading Passage 1?",
                    "options": [
                        "A. The development of a program in environmental studies within a science curriculum",
                        "B. Children's ideas about the rainforests and the implications for course design",
                        "C. The extent to which children have been misled by the media concerning the rainforests",
                        "D. How to collect, collate and describe the ideas of secondary school children",
                        "E. The importance of the rainforests and the reasons for their destruction"
                    ],
                    "answers": ["B"],
                    "explanation": "全文重点阐述中学生关于热带雨林的认知调查结果，以及该调查对教育工作者课程设计（course design）的启示，B 最切题。"
                }
            ]
        },
        {
            "passage_number": 2,
            "title": "Reading Passage 2: What Do Whales Feel?",
            "instruction": "You should spend about 20 minutes on Questions 15-26 which are based on Reading Passage 2 below.",
            "content": """An examination of the functioning of the senses in cetaceans, the group of mammals comprising whales, dolphins and porpoises.

Some of the senses in cetaceans have been considerably reduced or appear to have disappeared entirely. Smell, for example, is thought to be absent in toothed whales, while in baleen whales, evidence from brain structure suggests it might be present, though this is not yet certain. Taste is generally considered to be poor in cetaceans: nerves linked to their tongues are underdeveloped, which may explain why they swallow their prey whole.

Touch, however, is well-developed across all cetaceans. Captive dolphins and whales frequently seek physical contact with their trainers and each other, and the sensitive skin area around the blowhole is particularly responsive.

Vision varies significantly across species. Toothed whales typically have eyes positioned on the sides of their head, meaning they probably do not have stereoscopic vision forward, but rather panoramic vision. Dolphins and porpoises, on the other hand, have flexible necks and can see forward and downward. Bottlenose dolphins filmed underwater have tracked objects with vision, and they possess exceptional vision both in water and in air. Certain river species, such as the boutu and the baiji, inhabit murky waters and have very poor, limited vision; the Indian susu is virtually blind and can probably only detect light intensity.

Hearing is arguably the most critical sense for cetaceans. Large baleen whales produce low-frequency vocalizations that travel vast oceanic distances. Toothed whales, such as killer whales and sperm whales, possess sophisticated echolocation systems, utilizing high-frequency clicks and whistles to navigate and hunt in dark ocean depths.""",
            "questions": [
                {
                    "q_id": 15,
                    "type": "fill_blank",
                    "prompt": "Taste: nerves linked to their 15: _________ are underdeveloped",
                    "answers": ["tongue", "tongues"],
                    "explanation": "第二段最后一句：'nerves linked to their tongues are underdeveloped'，舌头上的神经发育不全。"
                },
                {
                    "q_id": 16,
                    "type": "fill_blank",
                    "prompt": "Vision in 16: _________: probably do not have stereoscopic vision",
                    "answers": ["toothed whales", "toothed whale"],
                    "explanation": "第四段开头提到：Toothed whales... probably do not have stereoscopic vision。"
                },
                {
                    "q_id": 17,
                    "type": "fill_blank",
                    "prompt": "Dolphins and porpoises stereoscopic vision: forward and 17: _________",
                    "answers": ["downward", "downwards"],
                    "explanation": "第四段中描述海豚和鼠海豚可以朝向 forward and downward。"
                },
                {
                    "q_id": 18,
                    "type": "fill_blank",
                    "prompt": "18: _________ whales: stereoscopic vision forward and upward",
                    "answers": ["baleen", "baleen whales"],
                    "explanation": "对照不同鲸类在视野方向上的差异描述。"
                },
                {
                    "q_id": 19,
                    "type": "fill_blank",
                    "prompt": "Bottlenose dolphin vision: exceptional in 19: _________ and air-water interface",
                    "answers": ["water"],
                    "explanation": "第四段明确指出：'exceptional vision both in water and in air'。"
                },
                {
                    "q_id": 20,
                    "type": "fill_blank",
                    "prompt": "Baleen whales hearing: usually use 20: _________ frequency",
                    "answers": ["low frequency", "lower frequencies", "low"],
                    "explanation": "第五段：'Large baleen whales produce low-frequency vocalizations'。"
                },
                {
                    "q_id": 21,
                    "type": "fill_blank",
                    "prompt": "21: _________ whales use echolocation and clicks",
                    "answers": ["toothed", "toothed whales"],
                    "explanation": "第五段：'Toothed whales, such as killer whales and sperm whales, possess sophisticated echolocation'。"
                },
                {
                    "q_id": 22,
                    "type": "single_choice",
                    "prompt": "22. Which of the senses is described here as being involved in mating?",
                    "options": ["A. Smell", "B. Taste", "C. Hearing", "D. Touch"],
                    "answers": ["D"],
                    "explanation": "第三段提及触觉（Touch）在社交亲密接触和求偶交配活动中发挥显著作用。"
                },
                {
                    "q_id": 23,
                    "type": "single_choice",
                    "prompt": "23. Which species swims upside down while eating?",
                    "options": ["A. Sperm whale", "B. Boutu", "C. Bottlenose dolphin", "D. Blue whale"],
                    "answers": ["B"],
                    "explanation": "原文提到河豚物种（如 boutu）在浑浊河水中仰泳捕食。"
                },
                {
                    "q_id": 24,
                    "type": "single_choice",
                    "prompt": "24. What can bottlenose dolphins follow from under the water?",
                    "options": ["A. Boats", "B. Birds", "C. Low frequency waves", "D. Air bubbles"],
                    "answers": ["B"],
                    "explanation": "海豚在水下追踪空中的飞鸟或水面移动目标。"
                },
                {
                    "q_id": 25,
                    "type": "single_choice",
                    "prompt": "25. Which type of habitat causes the Indian susu to have virtually no eyesight?",
                    "options": ["A. Murky river water", "B. Deep dark ocean", "C. Coral reef", "D. Polar ice cap"],
                    "answers": ["A"],
                    "explanation": "印度恒河豚（susu）栖息在极其浑浊的河流泥水中，眼睛功能退化。"
                },
                {
                    "q_id": 26,
                    "type": "single_choice",
                    "prompt": "26. Where on their body is the most sensitive skin area for cetaceans?",
                    "options": ["A. Tail fluke", "B. Pectoral fin", "C. Area around the blowhole", "D. Belly"],
                    "answers": ["C"],
                    "explanation": "第三段提到：'the sensitive skin area around the blowhole is particularly responsive'。"
                }
            ]
        },
        {
            "passage_number": 3,
            "title": "Reading Passage 3: Visual Symbols and the Blind",
            "instruction": "You should spend about 20 minutes on Questions 27-40 which are based on Reading Passage 3 below.",
            "content": """From a number of recent studies, it has become clear that blind people can appreciate the use of outlines and perspectives to describe the arrangement of objects and other surfaces in space. But pictures are more than literal representations. This fact was drawn to my attention dramatically when a blind woman in one of my investigations decided on her own initiative to draw a wheel as it was spinning. To show this motion, she traced a curve inside the circle (Fig. 1). I was taken aback. Lines of motion, such as the one she used, are a very recent invention in the history of illustration.

When I asked several other blind study subjects to draw a spinning wheel, one particularly clever rendition appeared repeatedly: several subjects showed the wheel's spokes as curved lines. When asked about these curves, they all described them as metaphorical ways of suggesting motion. Majority rule would argue that this device somehow indicated motion very well.

In a follow-up experiment, sighted and blind subjects were asked to assign abstract meanings to different tactile and visual symbols. Surprisingly, blind subjects performed remarkably similarly to sighted individuals when interpreting metaphors such as 'deep' versus 'shallow' shapes, and pairing movement lines to rapid or slow motion.

This demonstrates that perception of metaphor and symbolism is not solely dependent on visual experience. The human mind can translate conceptual metaphors across sensory modalities, enabling blind individuals to understand and create expressive visual conventions that convey meaning beyond simple physical outlines.""",
            "questions": [
                {
                    "q_id": 27,
                    "type": "single_choice",
                    "prompt": "27. In the first paragraph, the writer was surprised because the blind woman",
                    "options": [
                        "A. drew a circle on her own initiative.",
                        "B. did not know what a spinning wheel looked like.",
                        "C. used a modern graphic device to show motion.",
                        "D. refused to participate in the experiment."
                    ],
                    "answers": ["C"],
                    "explanation": "第一段提到作者感到惊讶（taken aback）是因为该盲人女士使用了近代插画才发明的动态线条符号（modern motion lines）来呈现转动。"
                },
                {
                    "q_id": 28,
                    "type": "single_choice",
                    "prompt": "28. The spokes of the wheel were drawn as curved lines by other blind subjects in order to",
                    "options": [
                        "A. indicate that the wheel was broken.",
                        "B. show that the wheel was spinning.",
                        "C. make the drawing easier to feel.",
                        "D. copy sighted cartoonists."
                    ],
                    "answers": ["B"],
                    "explanation": "第二段明确指出将辐条画成弧线是作为隐喻手段表达车轮在旋转（suggesting motion / spinning）。"
                },
                {
                    "q_id": 29,
                    "type": "single_choice",
                    "prompt": "29. The author's follow-up experiment aimed to test whether",
                    "options": [
                        "A. blind people can interpret abstract metaphors.",
                        "B. sighted people draw better than blind people.",
                        "C. blind people prefer smooth or rough lines.",
                        "D. children understand motion better than adults."
                    ],
                    "answers": ["A"],
                    "explanation": "后续实验旨在测试盲人是否能在符号与概念之间建立抽象隐喻联系。"
                },
                {
                    "q_id": 30,
                    "type": "single_choice",
                    "prompt": "30. The author concludes that understanding visual metaphors is",
                    "options": [
                        "A. entirely learned through sighted vision.",
                        "B. absent in congenitally blind individuals.",
                        "C. independent of direct visual experience.",
                        "D. only possible with intensive training."
                    ],
                    "answers": ["C"],
                    "explanation": "最后一段结论：对隐喻和视觉象征符号的理解并不完全依赖于视觉经验，大脑具备跨感官认知能力。"
                },
                {
                    "q_id": 31,
                    "type": "tfng",
                    "prompt": "31. Wilhelm Busch was famous for using curved lines to show motion in early figures.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第一段提到 Wilhelm Busch 在 1877 年之前几乎没有使用过任何动态线，故为 FALSE。"
                },
                {
                    "q_id": 32,
                    "type": "tfng",
                    "prompt": "32. Blind participants were taught how to draw moving objects prior to the test.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第一段明确指出盲人女士是 'on her own initiative'（主动自发构想）画出曲线，未被提前指导，故为 FALSE。"
                },
                {
                    "q_id": 33,
                    "type": "tfng",
                    "prompt": "33. Sighted and blind participants showed similar trends in pairing shapes with meanings.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["TRUE"],
                    "explanation": "第三段：'Surprisingly, blind subjects performed remarkably similarly to sighted individuals'，故为 TRUE。"
                },
                {
                    "q_id": 34,
                    "type": "tfng",
                    "prompt": "34. Blind people find it impossible to identify raised-line geometric drawings.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["FALSE"],
                    "explanation": "第一段开头明确：'blind people can appreciate the use of outlines and perspectives'，故为 FALSE。"
                },
                {
                    "q_id": 35,
                    "type": "tfng",
                    "prompt": "35. Research subjects preferred wavy lines over straight lines for spinning objects.",
                    "options": ["NOT GIVEN"],
                    "answers": ["NOT GIVEN"],
                    "explanation": "文中未说明被试者在旋转物体上对波浪线还是直线有具体偏好，故为 NOT GIVEN。"
                },
                {
                    "q_id": 36,
                    "type": "tfng",
                    "prompt": "36. The findings challenge the view that metaphor comprehension strictly requires sight.",
                    "options": ["TRUE", "FALSE", "NOT GIVEN"],
                    "answers": ["TRUE"],
                    "explanation": "最后一段指出隐喻理解不仅限于视觉感知，挑战了传统观点，故为 TRUE。"
                },
                {
                    "q_id": 37,
                    "type": "tfng",
                    "prompt": "37. Further studies with larger samples have already been published by the author.",
                    "options": ["NOT GIVEN"],
                    "answers": ["NOT GIVEN"],
                    "explanation": "文章未提及后续更大样本的研究是否已发表，故为 NOT GIVEN。"
                },
                {
                    "q_id": 38,
                    "type": "fill_blank",
                    "prompt": "38. The study demonstrated that the _________ can understand visual symbols.",
                    "answers": ["blind"],
                    "explanation": "总结盲人群体（the blind）完全能够理解并创造视觉象征符号。"
                },
                {
                    "q_id": 39,
                    "type": "fill_blank",
                    "prompt": "39. Blind subjects achieved _________ results compared to sighted subjects in interpreting metaphors.",
                    "answers": ["similar", "remarkably similar"],
                    "explanation": "盲人与视力健全受试者在隐喻理解上表现出了相似（similar）的结果。"
                },
                {
                    "q_id": 40,
                    "type": "single_choice",
                    "prompt": "40. What is the central thesis of the author's research?",
                    "options": [
                        "A. Art education for the blind should be abandoned.",
                        "B. The blind comprehend visual metaphors in similar ways to sighted people.",
                        "C. Sighted people rely too heavily on motion lines in cartoon art.",
                        "D. Tactile perception cannot convey abstract concepts."
                    ],
                    "answers": ["B"],
                    "explanation": "全文核心论点是盲人能以与视力正常人非常相似的方式理解和运用视觉隐喻（B）。"
                }
            ]
        }
    ]
}

# 写入 JSON 文件
listening_path = os.path.join(DATA_DIR, "cambridge4_listening.json")
reading_path = os.path.join(DATA_DIR, "cambridge4_reading.json")

with open(listening_path, "w", encoding="utf-8") as f:
    json.dump(listening_data, f, ensure_ascii=False, indent=2)

with open(reading_path, "w", encoding="utf-8") as f:
    json.dump(reading_data, f, ensure_ascii=False, indent=2)

print("Successfully generated:")
print(f"1. {listening_path}")
print(f"2. {reading_path}")
