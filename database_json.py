import json
import re


def split_pinyin(py_str):
    """从原始拼音字符串拆分声母、韵母、声调"""
    # 分离声调（支持数字和符号标记）
    tone = 5
    if py_str[-1].isdigit():
        tone = int(py_str[-1])
        clean_py = py_str[:-1]
    else:
        tone_map = {'ā': 1, 'á': 2, 'ǎ': 3, 'à': 4,
                    'ē': 1, 'é': 2, 'ě': 3, 'è': 4,
                    'ī': 1, 'í': 2, 'ǐ': 3, 'ì': 4,
                    'ō': 1, 'ó': 2, 'ǒ': 3, 'ò': 4,
                    'ū': 1, 'ú': 2, 'ǔ': 3, 'ù': 4,
                    'ǖ': 1, 'ǘ': 2, 'ǚ': 3, 'ǜ': 4}
        for char in py_str:
            if char in tone_map:
                tone = tone_map[char]
                break
        clean_py = re.sub(r'[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]', '', py_str)

    # 处理 ü 的特殊情况
    clean_py = clean_py.replace("ü", "v").replace("ǖ", "v").replace("ǘ", "v").replace("ǚ", "v").replace("ǜ", "v")

    # 分离声母和韵母
    initial = ""
    if clean_py.startswith('zh'):
        initial = 'zh'
        final = clean_py[2:]
    elif clean_py.startswith(('ch', 'sh')):
        initial = clean_py[:2]
        final = clean_py[2:]
    else:
        initial = clean_py[0] if clean_py and clean_py[0] in 'bpmfdtnlgkhjqxzcsryw' else ''
        final = clean_py[len(initial):]

    return initial, final, tone


def process_idiom(raw):
    """处理单个成语（完全使用原始拼音数据）"""
    word = raw["word"]

    # 拆分原始拼音字段
    try:
        pinyin_list = raw["pinyin"].split()
        if len(pinyin_list) != 4:
            print(f"拼音格式错误: {word} - {raw['pinyin']}")
            return None
    except KeyError:
        print(f"缺失拼音字段: {word}")
        return None

    # 构建字符详情
    characters = []
    for idx, (char, py) in enumerate(zip(word, pinyin_list), 1):
        initial, final, tone = split_pinyin(py.lower())

        characters.append({
            "char": char,
            "initial": initial,
            "final": final,
            "tone": tone,
            "position": idx
        })

    return {
        "word": word,
        "pinyin": raw["pinyin"],  # 保留原始带声调拼音
        "pinyin_r": raw["pinyin_r"],  # 保留无数字声调拼音
        "abbreviation": raw["abbreviation"],  # 直接使用原始缩写
        "characters": characters,
        "explanation": raw["explanation"],
        "source": raw.get("derivation", ""),
        "example": raw.get("example", "")
    }


def build_indexes(data):
    """构建查询索引（增强版）"""
    indexes = {
        "by_initials": {},
        "by_character": {},
        "by_initial_final": {}
    }

    for word, info in data.items():
        # 首字母缩写索引
        indexes["by_initials"].setdefault(info["abbreviation"], []).append(word)

        # 单字索引
        for char_info in info["characters"]:
            char = char_info["char"]
            indexes["by_character"].setdefault(char, []).append(word)

            # 声母+韵母组合索引
            key = f"{char_info['initial']}_{char_info['final']}"
            indexes["by_initial_final"].setdefault(key, []).append(word)

    return indexes


# 原始数据转换
with open("idiom.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

processed_data = {}
error_log = []

for item in raw_data:
    # 基础校验
    if len(item.get("word", "")) != 4:
        error_log.append(f"无效成语字数: {item.get('word', '未知')}")
        continue

    try:
        processed = process_idiom(item)
        if processed:
            processed_data[processed["word"]] = processed
        else:
            error_log.append(f"处理失败: {item['word']}")
    except Exception as e:
        error_log.append(f"处理异常: {item.get('word', '未知')} - {str(e)}")

# 保存主数据
with open("idioms_data.json", "w", encoding="utf-8") as f:
    json.dump(processed_data, f, ensure_ascii=False, indent=2)

# 构建并保存索引
indexes = build_indexes(processed_data)
with open("indexes.json", "w", encoding="utf-8") as f:
    json.dump(indexes, f, ensure_ascii=False, indent=2)

# 输出错误日志
if error_log:
    print(f"处理完成，发现 {len(error_log)} 条错误:")
    with open("processing_errors.log", "w", encoding="utf-8") as f:
        f.write("\n".join(error_log))
else:
    print("全部数据处理成功！")