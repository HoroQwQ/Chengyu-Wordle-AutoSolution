# Chengyu-Wordle-AutoSolution
一个基于chinese-xinhua项目为数据库的汉字Wordle（四字成语猜测问题）自动化解题器。通过加载成语数据库，结合成语的拼音特征（声母、韵母、声调）以及用户提供的反馈，逐步缩小候选集范围，最终得出正确答案。
## 数据库及其来源
数据来源于中华新华字典项目，链接：https://github.com/pwxcoo/chinese-xinhua

首先通过运行database_json.py创建搜索数据库idiom_data.json,其具体格式为：
```json
[
    {
  "阿鼻地狱": {
    "word": "阿鼻地狱",
    "pinyin": "ā bí dì yù",
    "pinyin_r": "a bi di yu",
    "abbreviation": "abdy",
    "characters": [
      {
        "char": "阿",
        "initial": "",
        "final": "",
        "tone": 1,
        "position": 1
      },
      {
        "char": "鼻",
        "initial": "b",
        "final": "",
        "tone": 2,
        "position": 2
      },
      {
        "char": "地",
        "initial": "d",
        "final": "",
        "tone": 4,
        "position": 3
      },
      {
        "char": "狱",
        "initial": "y",
        "final": "",
        "tone": 4,
        "position": 4
      }
    ],
    "explanation": "阿鼻梵语的译音，意译为无间”，即痛苦无有间断之意。常用来比喻黑暗的社会和严酷的牢狱。又比喻无法摆脱的极其痛苦的境地。",
    "source": "语出《法华经·法师功德品》下至阿鼻地狱。”",
    "example": "但也有少数意志薄弱的……逐步上当，终至堕入～。★《上饶集中营·炼狱杂记》"
  },
    ...
]
```
## 求解器的实现
###  1. 数据加载
程序会从指定的 JSON 文件中加载成语数据库，每个成语包含以下信息：
- **声母**（`initial`）
- **韵母**（`final`）
- **声调**（`tone`）

数据加载代码：
```python
with open(db_path, 'r', encoding='utf-8') as f:
    self.idioms_db = json.load(f)
```
### 2. 用户反馈解析
解析过程代码：
```python
if code == '1':  # 绿色反馈
    feedback_dict['green'][value].append(pos)
elif code == '2':  # 橙色反馈
    feedback_dict['orange'][value].append(pos)
elif code == '0':  # 灰色反馈
    if pos not in [p for positions in feedback_dict['green'].values() for p in positions]:
        feedback_dict['gray'].add(value)
```
### 3. 候选成语过滤
过滤逻辑：
```python
if values[pos] != val:  # 不满足绿色约束
    return False

if values[pos] == val:  # 违反橙色约束
    return False

if values.count(val) > allowed:  # 超过灰色限制
    return False
```
搜索原理：
1. 初始猜测:程序通过启发式算法生成第一个猜测。
2. 稀有度启发式算法:为提高效率，程序优先猜测包含“稀有声母/韵母/声调”的成语。稀有度得分计算公式：

$$
\text{score} = \frac{1}{\text{frequency}[c_{\text{initial}}] + 10^{-6}} + 
\frac{1}{\text{frequency}[c_{\text{final}}] + 10^{-6}} + 
\frac{1}{\text{frequency}[c_{\text{tone}}] + 10^{-6}}
$$

得分越高的成语被优先选为下一轮猜测。

使用示例

```python
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

    if len(remaining) == 1
```
## 许可证

该项目基于 MIT 许可证进行开源，详情请参阅 LICENSE 文件。


