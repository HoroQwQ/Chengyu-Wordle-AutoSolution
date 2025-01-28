import json
from collections import defaultdict


class IdiomSolverPro:
    def __init__(self, db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            self.idioms = json.load(f)
        self.candidates = list(self.idioms.values())

    def process_feedback(self, guess_word, tone_fb, initial_fb, final_fb):
        try:
            guess_data = self.idioms[guess_word]
        except KeyError:
            raise ValueError(f"成语 {guess_word} 不存在")

        new_candidates = []
        for candidate in self.candidates:
            valid = self._validate_candidate(candidate, guess_data, {
                'tone': tone_fb,
                'initial': initial_fb,
                'final': final_fb
            })
            if valid:
                new_candidates.append(candidate)

        self.candidates = new_candidates
        return len(self.candidates)

    def _validate_candidate(self, candidate, guess_data, patterns):
        # 并行检查三类属性
        return all(
            self._check_single_attribute(
                attr_type=c_type,
                candidate=[c[attr] for c in candidate['characters']],
                guess=[c[attr] for c in guess_data['characters']],
                pattern=patterns[c_type]
            ) for c_type, attr in [
                ('tone', 'tone'),
                ('initial', 'initial'),
                ('final', 'final')
            ]
        )

    def _check_single_attribute(self, attr_type, candidate, guess, pattern):
        # 转换声调为字符串
        if attr_type == 'tone':
            candidate = [str(c) for c in candidate]
            guess = [str(g) for g in guess]

        green_pos = set()
        orange_req = defaultdict(int)
        gray_vals = set()

        # 阶段1：收集反馈信息
        for i, code in enumerate(pattern):
            if code == '1':
                if candidate[i] != guess[i]:
                    return False
                green_pos.add(i)
            elif code == '2':
                if candidate[i] == guess[i]:
                    return False
                orange_req[guess[i]] += 1
            elif code == '0':
                gray_vals.add(guess[i])

        # 阶段2：验证橙色需求
        available = defaultdict(int)
        for i, val in enumerate(candidate):
            if i not in green_pos:
                available[val] += 1

        for val, req in orange_req.items():
            if available.get(val, 0) < req:
                return False

        # 阶段3：验证灰色条件
        for gray_val in gray_vals:
            # 检查非绿色位置是否存在该值
            if any(candidate[i] == gray_val for i in range(4) if i not in green_pos):
                return False
            # 检查总出现次数不超过绿色位置次数
            total_count = candidate.count(gray_val)
            green_count = sum(1 for i in green_pos if candidate[i] == gray_val)
            if total_count > green_count:
                return False

        return True

    def get_suggestion(self):
        """基于信息熵的优化猜测策略"""
        if not self.candidates:
            return None

        # 统计属性频率
        freq = defaultdict(lambda: defaultdict(int))
        for idiom in self.candidates:
            for i in range(4):
                freq['char'][idiom['characters'][i]['char']] += 1
                freq['initial'][idiom['characters'][i]['initial']] += 1
                freq['final'][idiom['characters'][i]['final']] += 1
                freq['tone'][str(idiom['characters'][i]['tone'])] += 1

        # 计算候选得分
        best_score = -1
        best_idiom = self.candidates[0]
        for idiom in self.candidates:
            score = 0
            for i in range(4):
                c = idiom['characters'][i]
                score += 1 / (freq['char'][c['char']] ** 0.5)
                score += 1 / (freq['initial'][c['initial']] ** 0.5)
                score += 1 / (freq['final'][c['final']] ** 0.5)
                score += 1 / (freq['tone'][str(c['tone'])] ** 0.5)
            if score > best_score:
                best_score = score
                best_idiom = idiom
        return best_idiom['word']

# 使用示例
if __name__ == "__main__":
    solver = IdiomSolverPro('idioms_data.json')

    while True:
        user_input = input("请输入本轮结果（格式：成语 音调反馈 声母反馈 韵母反馈）：").strip()
        if user_input.lower() == 'exit':
            break

        try:
            parts = user_input.split()
            if len(parts) != 4:
                raise ValueError("输入格式错误，需要4个参数")

            guess_word, tone_fb, initial_fb, final_fb = parts
            remaining = solver.process_feedback(guess_word, tone_fb, initial_fb, final_fb)

            print(f"剩余候选数：{remaining}")

            if remaining == 0:
                print("错误：没有候选词剩余")
                break
            elif remaining == 1:
                print(f"最终答案：{solver.candidates[0]['word']}")
                break

            print(f"建议下次猜测：{solver.get_suggestion()}")

        except Exception as e:
            print(f"发生错误：{str(e)}")
