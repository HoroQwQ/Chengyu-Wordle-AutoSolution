import json
from collections import defaultdict


class IdiomSolver:
    def __init__(self, db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            self.idioms_db = json.load(f)
        self.candidates = list(self.idioms_db.values())
        self.attribute_maps = {
            'initial': [c['initial'] for c in self.idioms_db['阿鼻地狱']['characters']],
            'final': [c['final'] for c in self.idioms_db['阿鼻地狱']['characters']],
            'tone': [str(c['tone']) for c in self.idioms_db['阿鼻地狱']['characters']]
        }

    def parse_feedback(self, guess_word, tone_fb, initial_fb, final_fb):
        """将数字反馈转换为结构化的过滤条件"""
        feedback = {
            'tone': {'green': defaultdict(list), 'orange': defaultdict(list), 'gray': set()},
            'initial': {'green': defaultdict(list), 'orange': defaultdict(list), 'gray': set()},
            'final': {'green': defaultdict(list), 'orange': defaultdict(list), 'gray': set()}
        }

        guess_data = self.idioms_db[guess_word]['characters']

        # 解析声母反馈
        for pos, code in enumerate(initial_fb):
            attr = guess_data[pos]['initial']
            self._process_code(feedback['initial'], code, pos, attr)

        # 解析韵母反馈
        for pos, code in enumerate(final_fb):
            attr = guess_data[pos]['final']
            self._process_code(feedback['final'], code, pos, attr)

        # 解析声调反馈（转为字符串比较）
        for pos, code in enumerate(tone_fb):
            attr = str(guess_data[pos]['tone'])
            self._process_code(feedback['tone'], code, pos, attr)

        return feedback

    def _process_code(self, feedback_dict, code, pos, value):
        """处理单个反馈码（核心逻辑）"""
        if code == '1':
            feedback_dict['green'][value].append(pos)
        elif code == '2':
            feedback_dict['orange'][value].append(pos)
        elif code == '0':
            # 只有当该值没有绿色反馈时才加入gray
            if pos not in [p for positions in feedback_dict['green'].values() for p in positions]:
                feedback_dict['gray'].add(value)

    def filter_candidates(self, feedback):
        """根据反馈过滤候选词"""
        new_candidates = []
        for candidate in self.candidates:
            if self._is_valid_candidate(candidate, feedback):
                new_candidates.append(candidate)
        self.candidates = new_candidates
        return self.candidates

    def _is_valid_candidate(self, candidate, feedback):
        """检查候选词是否符合所有反馈条件"""
        attrs = {
            'initial': [c['initial'] for c in candidate['characters']],
            'final': [c['final'] for c in candidate['characters']],
            'tone': [str(c['tone']) for c in candidate['characters']]
        }

        for attr_type in ['initial', 'final', 'tone']:
            if not self._check_attribute(
                    attrs[attr_type],
                    feedback[attr_type]['green'],
                    feedback[attr_type]['orange'],
                    feedback[attr_type]['gray']
            ):
                return False
        return True

    def _check_attribute(self, values, green, orange, gray):
        """检查单个属性（声母/韵母/声调）的约束"""
        # 检查绿色约束
        for val, positions in green.items():
            for pos in positions:
                if values[pos] != val:
                    return False

        # 检查橙色约束
        for val, positions in orange.items():
            # 确保不在指定位置出现
            for pos in positions:
                if values[pos] == val:
                    return False
            # 计算最小需要出现的次数
            min_required = len(positions)
            actual_count = sum(1 for v in values if v == val)
            if actual_count < min_required:
                return False

        # 检查灰色约束
        for val in gray:
            # 允许的绿色出现次数
            allowed = len(green.get(val, []))
            if values.count(val) > allowed:
                return False

        return True

    def make_guess(self):
        """选择最优猜测（基于候选词频率的启发式算法）"""
        if not self.candidates:
            return None

        # 优先选择包含稀有元素的候选词
        frequency = defaultdict(int)
        for candidate in self.candidates:
            for c in candidate['characters']:
                frequency[c['initial']] += 1
                frequency[c['final']] += 1
                frequency[str(c['tone'])] += 1

        # 计算每个候选词的稀有度得分
        best_score = -1
        best_candidate = self.candidates[0]

        for candidate in self.candidates:
            score = 0
            for c in candidate['characters']:
                score += 1 / (frequency[c['initial']] + 1e-6)
                score += 1 / (frequency[c['final']] + 1e-6)
                score += 1 / (frequency[str(c['tone'])] + 1e-6)
            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate['word']


# 使用示例
if __name__ == "__main__":
    solver = IdiomSolver('idioms_data.json')

    # 初始猜测
    print("初始猜测:", solver.make_guess())

    # 模拟游戏过程
    while True:
        # 用户输入格式：成语 音调反馈 声母反馈 韵母反馈
        user_input = input("请输入本轮结果（格式：成语 音调反馈 声母反馈 韵母反馈）：")
        if user_input.lower() == 'exit':
            break

        guess_word, tone_fb, initial_fb, final_fb = user_input.split()

        # 解析反馈
        feedback = solver.parse_feedback(guess_word, tone_fb, initial_fb, final_fb)

        # 过滤候选
        remaining = solver.filter_candidates(feedback)
        print(f"剩余候选数：{len(remaining)}")

        if len(remaining) == 1:
            print(f"\n最终答案：{remaining[0]['word']}")
            break

        # 生成下一轮猜测
        next_guess = solver.make_guess()
        print(f"\n建议下一轮猜测：{next_guess}\n")