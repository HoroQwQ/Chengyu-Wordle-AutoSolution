import json
import re

# 完善声调映射表（新增带调韵母处理）
TONAL_MAP = {
    'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
    'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
    'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
    'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
    'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
    'ǖ': 'ü', 'ǘ': 'ü', 'ǚ': 'ü', 'ǜ': 'ü',
    'ń': 'n', 'ň': 'n', 'ǹ': 'n'
}

# 所有合法声母集合（包含零声母）
INITIAL_SET = {
    '', 'b', 'p', 'm', 'f', 'd', 't', 'n', 'l', 'g', 'k', 'h',
    'j', 'q', 'x', 'zh', 'ch', 'sh', 'r', 'z', 'c', 's', 'y', 'w'
}

# 复合韵母优先级列表（长到短排序）
COMPOUND_FINALS = [
    'iang', 'iong', 'uang', 'ueng', 'uan', 'van', 'iao', 'ian',
    'uai', 'ing', 'ang', 'eng', 'ong', 'ai', 'ei', 'ao', 'ou',
    'ia', 'ie', 'iu', 'in', 'ua', 'uo', 'ui', 'un', 've', 'er'
]


def extract_tone(pinyin):
    """精确提取声调并返回无调拼音"""
    tone = 0
    clean_chars = []

    # 优先检查数字声调
    if pinyin[-1].isdigit():
        tone = int(pinyin[-1])
        clean_py = pinyin[:-1]
    else:
        # 处理符号声调
        for c in pinyin:
            if c in TONAL_MAP:
                clean_chars.append(TONAL_MAP[c])
                if tone == 0:
                    tone = {'ā': 1, 'á': 2, 'ǎ': 3, 'à': 4,
                            'ē': 1, 'é': 2, 'ě': 3, 'è': 4,
                            'ī': 1, 'í': 2, 'ǐ': 3, 'ì': 4,
                            'ō': 1, 'ó': 2, 'ǒ': 3, 'ò': 4,
                            'ū': 1, 'ú': 2, 'ǔ': 3, 'ù': 4,
                            'ǖ': 1, 'ǘ': 2, 'ǚ': 3, 'ǜ': 4}.get(c, 0)
            elif c.isalpha() or c == 'ü':
                clean_chars.append(c)
        clean_py = ''.join(clean_chars)

    return clean_py.replace('ü', 'v'), tone


def split_pinyin(pinyin):
    """精准拆分拼音三要素"""
    # 统一处理ü和v
    raw_py = pinyin.lower().replace('ü', 'v').replace('u:', 'v')

    # 步骤1：提取声调和清理拼音
    clean_py, tone = extract_tone(raw_py)

    # 步骤2：分离声母和韵母
    initial = ""
    final = clean_py

    # 处理特殊零声母开头
    if clean_py.startswith(('a', 'e', 'o')) or clean_py in ['ai', 'ei', 'ao', 'ou', 'an', 'en', 'ang', 'er']:
        return '', clean_py, tone

    # 优先匹配复合声母
    for dual in ['zh', 'ch', 'sh']:
        if clean_py.startswith(dual):
            initial = dual
            final = clean_py[len(dual):]
            return initial, final, tone

    # 匹配单声母
    if len(clean_py) > 0 and clean_py[0] in 'bpmfdtnlgkhjqxrzcsyw':
        initial = clean_py[0]
        final = clean_py[1:]

    # 步骤3：验证并修复韵母结构
    if initial in ['j', 'q', 'x'] and final.startswith('v'):
        final = final.replace('v', 'u')  # 居→ju→j+ü

    # 处理舌尖元音
    if initial in ['z', 'c', 's'] and final == 'i':
        final = 'ih'
    elif initial in ['zh', 'ch', 'sh', 'r'] and final == 'i':
        final = 'ih'

    return initial, final, tone


def process_idiom(raw):
    """处理单个成语条目"""
    try:
        # 基础校验
        if len(raw["word"]) != 4:
            return None

        pinyin_list = re.split(r'\s+', raw["pinyin"].strip())
        if len(pinyin_list) != 4:
            return None

        characters = []
        for idx, (char, py) in enumerate(zip(raw["word"], pinyin_list), 1):
            initial, final, tone = split_pinyin(py)

            # 后处理修正
            if initial == 'y':
                # 处理y开头的特殊规则
                if final.startswith('ü'):
                    final = final.replace('ü', 'u')
                elif final.startswith('i'):
                    final = final[1:]
                    initial = '' if final.startswith(('a', 'e')) else initial
            elif initial == 'w':
                # 处理w开头的特殊规则
                if final.startswith('u'):
                    final = final[1:]
                    initial = '' if final.startswith(('a', 'o')) else initial

            characters.append({
                "char": char,
                "initial": initial,
                "final": final,
                "tone": tone,
                "position": idx
            })

        return {
            "word": raw["word"],
            "pinyin": ' '.join([f"{py}{t}" for py, t in zip(pinyin_list, [c['tone'] for c in characters])]),
            "pinyin_initials": raw["abbreviation"],
            "characters": characters,
            "explanation": raw.get("explanation", ""),
            "source": raw.get("derivation", ""),
            "example": raw.get("example", "")
        }

    except Exception as e:
        print(f"处理失败: {raw['word']} - {str(e)}")
        return None


def main():
    with open("idiom.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    processed = {}
    errors = []

    for item in raw_data:
        result = process_idiom(item)
        if result:
            processed[result["word"]] = result
        else:
            errors.append(item["word"])

    # 保存结果
    with open("idioms_data.json", "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    # 示例输出验证
    sample = processed.get("阿鼻地狱", {})
    print("【示例输出】")
    print(json.dumps(sample, ensure_ascii=False, indent=2))

    if errors:
        print(f"\n发现错误条目：{len(errors)} 条")
        with open("errors_v2.log", "w") as f:
            f.write("\n".join(errors))


if __name__ == "__main__":
    main()
