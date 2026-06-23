---
name: "national-emblem-generator"
description: "Generates SVG code and images for fictional faction/kingdom/symbol emblems, flags and heraldry. Invoke when user asks to design, generate, or create national emblems, flags, faction symbols for fictional worldbuilding."
---

# 国家徽标/旗帜生成器 (National Emblem Generator)

用于**架空世界观**中势力徽标、国旗、军旗、纹章等象征符号的设计与生成。支持 SVG 代码生成和图片生成两种输出形式。

## 使用场景

- 为架空国家、王国、帝国设计国旗或徽标
- 为虚构组织、家族、势力设计纹章或符号
- 需要 SVG 格式用于网页/应用嵌入
- 需要图片格式用于文档/展示
- 参考现实世界的纹章学、旗帜学设计原则进行创作

## 核心能力

### 1. 设计咨询（必须提问至少 5 个问题）

**每次生成前必须向用户提问，至少覆盖以下 5 个维度（可多不可少）：**

1. **徽标边框形状** — 盾形、圆形、菱形、矩形（旗帜）、多边形、无边框等
2. **主要元素** — 徽标/旗帜中最核心的视觉符号（如龙、鹰、狮、剑、星、十字、齿轮、城堡等）
3. **次要元素** — 辅助装饰性元素（如花环、缎带、星辰边框、几何纹路、文字/箴言等）
4. **主题配色** — 主色调、辅助色（2-3 种颜色），以及每种颜色的象征含义
5. **势力设定与背景** — 该势力所属的架空世界观类型（东方/西方/科幻/奇幻/蒸汽朋克等）、文化原型、势力名

**可选补充问题（视情况追加）：**
- 核心理念/想传达的价值观（力量、智慧、自由、团结等）
- 构图风格倾向（简约现代 / 古典繁复 / 军事硬朗 / 神秘奇幻等）
- 输出形式偏好（SVG 代码 / 图片 / 两者都要）
- 是否有现实参考的旗帜或徽标风格

### 2. SVG 代码生成

遵循规范生成可直接使用的 SVG 代码：

- **文件结构**：使用 `<svg>` 根元素，包含 `viewBox="0 0 800 600"` 等标准属性
- **分层构建**：背景层 → 主要图形层（徽标主体）→ 装饰层 → 文字层（如有）
- **命名规范**：每个 `<g>` 分组使用 `id` 或 `class` 标注层次含义
- **颜色定义**：推荐使用 `<defs>` 中的渐变/图案定义，颜色使用十六进制
- **可扩展性**：输出支持响应式缩放的矢量图形

**参考结构示例**（具体内容根据设计需求变化）：

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <defs>
    <!-- 渐变、图案等定义 -->
  </defs>
  <!-- 背景 -->
  <!-- 主体徽标 -->
  <!-- 装饰元素 -->
  <!-- 文字（如有） -->
</svg>
```

#### 设计规范要求

生成 SVG 时必须遵守以下规范，否则 SVG 将无法正常渲染：

1. **使用标准 SVG 元素**：`<svg>`, `<g>`, `<path>`, `<circle>`, `<rect>`, `<polygon>`, `<line>`, `<text>`, `<defs>`, `<linearGradient>`, `<radialGradient>`, `<stop>`, `<filter>` 等
2. **样式写法**：优先使用属性写法（`fill="red"`），而非 CSS 内联样式；部分框架不支持 css 内联 fill
3. **尺寸单位**：使用 `viewBox` 定义坐标系，不使用绝对像素宽高
4. **文本处理**：如需文字，使用系统字体（`sans-serif`, `serif`, `monospace`），避免依赖外部字体文件
5. **路径数据**：`<path d="...">` 使用标准 SVG path 命令（M, L, C, Q, A, Z 等）
6. **兼容性**：避免使用较新的 SVG 特性（如 `<mask>` 需谨慎），确保在主流浏览器中兼容

### 3. 图片生成

提供两种图片生成方式：

#### 方式 A: 模型内置图片生成（优先）

如果当前模型支持图片生成，优先使用以下方式：
- **生成 prompt 结构**：
  ```
  [旗帜/徽标类型], [风格描述], [主要符号和构图], [色彩方案], [质感/效果]
  ```
- **图片尺寸选择**：`square_hd` / `square` / `portrait_4_3` / `landscape_4_3` / `landscape_16_9`

#### 方式 B: Python 脚本生成（备用）

如果模型不支持图片生成，使用配套的 Python 脚本 [`emblem_generator.py`](file:///e:\Myproject\Other\MySkill\.trae\skills\national-emblem-generator\scripts\emblem_generator.py)：

- **SVG → PNG 转换**（需要 `cairosvg`）：将 AI 生成的 SVG 代码保存为文件，再渲染为 PNG
- **直接生成旗帜/徽标图片**（仅需 `Pillow`）：无需 SVG 步骤，直接生成带条纹/符号的图片

**安装依赖**：
```bash
pip install -r .trae/skills/national-emblem-generator/scripts/requirements.txt
# 或只装 Pillow（大部分场景够用）
pip install Pillow
```

**执行方式**：
```bash
# 方式1: SVG → PNG 转换（需要 cairosvg）
# 先由 AI 生成 SVG 代码并保存到文件，然后：
python .trae/skills/national-emblem-generator/scripts/emblem_generator.py svg input.svg -o output.png

# 方式2: 生成简单旗帜（仅需 Pillow）
python .trae/skills/national-emblem-generator/scripts/emblem_generator.py flag \
  -o flag.png --colors "#1a1a2e" "#e94560" --pattern horizontal

# 方式3: 生成带中心符号的徽标（仅需 Pillow）
python .trae/skills/national-emblem-generator/scripts/emblem_generator.py emblem \
  -o emblem.png --colors "#0a0a2e" "#ffd700" --symbol star
```

**支持的符号**：`star`（星）、`circle`（圆）、`diamond`（菱形）、`cross`（十字）、`triangle`（三角）、`moon`（新月）、`sun`（太阳）

**支持的旗帜模式**：`single`（纯色）、`horizontal`（水平双色）、`vertical`（垂直双色）、`tricolor`（垂直三色）、`tricolor_h`（水平三色）、`bicolor_h`（水平双色）、`bicolor_v`（垂直双色）

### 4. 纹章学/旗帜学参考

提供架空设计时可参考的现实原则：

- **旗帜学原则**：
  - 保持简单（儿童能凭记忆画出来）
  - 使用有意义的符号
  - 2-3 种基本颜色（避免过多色彩）
  - 无文字或印章（文字倒过来就看不懂了）
  - 与其它旗帜有区分度

- **纹章学原则**：
  - 颜色的"反律法"（金属色不与金属色叠放，色彩不与色彩叠放）
  - 盾形布局的区划（四分、三角分割、垂直/水平分割等）
  - 纹章图记（狮、鹰、百合、城堡等的象征含义）

## 工作流程

1. **设计咨询（必问 5 个问题）**：按上述 5 个必问维度向用户提问，收集完整设计需求
2. **方案确认**：将用户的回答汇总为设计概要，请用户确认
3. **SVG 生成**：根据确认的设计概要生成 SVG 代码
4. **迭代优化**：根据用户反馈调整设计
5. **图片输出**：
   - 如果模型支持图片生成 → 直接生成
   - 否则 → 使用 [`emblem_generator.py`](file:///e:\Myproject\Other\MySkill\.trae\skills\national-emblem-generator\scripts\emblem_generator.py) 脚本将 SVG 渲染为 PNG，或直接用 Pillow 生成图片

## 使用示例

**用户输入**："帮我设计一个蒸汽朋克风格的海盗联邦国旗"
**你的流程**：
1. 依次提问 5 个问题：
   - "边框形状：你希望旗帜是什么形状？矩形还是燕尾形？"
   - "主要元素：海盗联邦最核心的视觉符号是什么？齿轮、船锚、还是骷髅？"
   - "次要元素：是否需要边框花纹、缎带或文字作装饰？"
   - "主题配色：主色调和辅助色是什么？比如铜锈绿、铁锈红、蒸汽白？"
   - "势力设定：这个海盗联邦的文化原型是欧洲风还是东亚风？时代背景如何？"
2. 汇总设计概要请用户确认
3. 生成 SVG 代码并展示
4. 根据反馈调整
5. 如需图片 → 模型支持则生成 prompt，否则用脚本渲染

**用户输入**："为我的奇幻小说中的精灵王国设计一个徽标"
**你的流程**：
1. 依次提问 5 个问题：
   - "边框形状：徽标采用什么形状？盾形、圆形还是菱形？"
   - "主要元素：精灵王国最核心的符号是什么？树叶、星辰、弓还是水晶？"
   - "次要元素：需要花环、魔法纹路或精灵文字作装饰吗？"
   - "主题配色：主色调是什么？自然色系还是星月主题的银紫配色？"
   - "势力设定：是森林精灵、高等精灵还是黑暗精灵？文化风格偏向凯尔特还是东方？"
2. 汇总设计概要请用户确认
3. 生成 SVG 代码
4. 提供设计说明，解释各元素的象征含义
5. 如需图片 → 根据模型能力选择图片生成方式

**用户输入**："我的模型不支持生成图片，帮我生成一个简单的双色旗帜"
**你的流程**：
1. 虽然用户只需要简单图片，仍需按 5 个问题快速了解需求：
   - "边框形状：旗帜用标准矩形还是燕尾形？"
   - "主要元素：是否需要在旗帜中间加一个符号？比如星、十字、圆形？"
   - "次要元素：需要加边框或条纹装饰吗？"
   - "主题配色：两种颜色是什么？比如红底白星？"
   - "势力设定：这个代表什么势力？方便我设计合适的配色和符号"
2. 确定参数后，直接通过 `emblem_generator.py flag` 或 `emblem` 命令生成图片
3. 向用户展示生成的 PNG 图片路径
