import json
from collections import defaultdict


class IdiomSolver:
    def __init__(self, db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            self.idioms_db = json.load(f)
        self.candidates = list(self.idioms_db.values())

    def process_feedback(self, guess_word, tone_fb, initial_fb, final_fb):
        guess_data = self.idioms_db[guess_word]
        new_candidates = []

        # 同时处理三类反馈
        for candidate in self.candidates:
            valid = self._check_candidate(
                candidate,
                guess_data,
                tone_fb,
                initial_fb,
                final_fb
            )
            if valid:
                new_candidates.append(candidate)

        self.candidates = new_candidates
        return len(self.candidates)

    def _check_candidate(self, candidate, guess_data, tone_fb, initial_fb, final_fb):
        # 并行检查三类属性
        return (
                self._check_attribute(candidate, guess_data, 'tone', tone_fb) and
                self._check_attribute(candidate, guess_data, 'initial', initial_fb) and
                self._check_attribute(candidate, guess_data, 'final', final_fb)
        )

    def _check_attribute(self, candidate, guess_data, attr_type, pattern):
        guess_values = [str(c[attr_type]) if attr_type == 'tone' else c[attr_type]
                        for c in guess_data['characters']]
        candidate_values = [str(c[attr_type]) if attr_type == 'tone' else c[attr_type]
                            for c in candidate['characters']]

        # 阶段1：绿色验证
        green_positions = set()
        for i, code in enumerate(pattern):
            if code == '1':
                if candidate_values[i] != guess_values[i]:
                    return False
                green_positions.add(i)

        # 阶段2：橙色验证
        orange_required = defaultdict(int)
        for i, code in enumerate(pattern):
            if code == '2':
                if candidate_values[i] == guess_values[i]:
                    return False
                orange_required[guess_values[i]] += 1

        # 统计可用橙色值（排除绿色位置）
        available = defaultdict(int)
        for i, val in enumerate(candidate_values):
            if i not in green_positions:
                available[val] += 1

        for val, req in orange_required.items():
            if available.get(val, 0) < req:
                return False

        # 阶段3：灰色验证
        for i, code in enumerate(pattern):
            if code == '0':
                gray_val = guess_values[i]
                if any(candidate_values[j] == gray_val for j in range(4) if j not in green_positions):
                    return False

        return True

    def get_suggestion(self):
        """获取优化后的猜测建议"""
        if not self.candidates:
            return None
        # 优先选择包含最多绿色可能性的候选
        return self.candidates[0]['word']


# 使用示例
if __name__ == "__main__":
    solver = IdiomSolver('idioms_data.json')

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
