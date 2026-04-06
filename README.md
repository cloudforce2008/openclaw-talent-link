# OpenClaw Talent Link

> 基于 OpenClaw 生态的数字人才市场平台 — 让每一个配置精良的 Agent 都能成为"数字员工"，通过标准化接口实现能力的商业化变现。

## 🎯 项目愿景

**"雇佣数字员工的第一站"** —— 一个连接"会养 Agent 的人"和"需要 Agent 能力的人"的平台。

## 📦 核心数字员工

| 员工 | 定位 | 阶段 |
| :--- | :--- | :--- |
| 📈 股票分析员 | A 股实时行情、多源数据交叉验证、7-Agent 深度分析 | 🚧 开发中 |
| 🛡️ 保险经纪人助理 | 跨学科 RAG、家庭画像、主动关系维护 | 📋 规划中 |
| ✍️ 内容创作者助手 | 风格指纹克隆、多平台自适应重构 | 📋 规划中 |

## 🏗️ 技术架构

```
用户交互层 (Web / 微信 / 飞书 / 钉钉)
    ↓
平台网关 (Omni-Channel Gateway)
    ↓
OpenClaw Runtime (session_spawn 沙箱隔离)
    ↓
数字员工 Agents + Skills 注册表 + 记忆与进化引擎
```

## 📁 目录结构

```
openclaw-talent-link/
├── src/talent_link/
│   ├── agents/              # 数字员工核心逻辑
│   │   └── stock_analyst.py  # 🚀 股票分析员 (MVP)
│   ├── skills/              # 可复用技能模块
│   │   ├── akshare_wrapper.py  # A股数据获取
│   │   └── feishu_card.py      # 飞书/微信卡片渲染
│   ├── platform/            # 平台基建 (TODO)
│   └── memory/              # 记忆系统 (TODO)
├── tests/                    # 测试用例
├── docs/                    # 文档
└── scripts/                 # 工具脚本
```

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/cloudforce2008/openclaw-talent-link.git
cd openclaw-talent-link

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 运行股票分析测试
python -m src.talent_link.agents.stock_analyst
```

## 📊 股票分析员 (MVP)

### 核心功能

- **7-Agent 多智能体分析**: 技术面 / 基本面 / 情绪面 / 看多辩论 / 看空辩论 / 交易信号 / 风控审核
- **A 股数据源**: 基于 AkShare 获取实时行情、资金流向、龙虎榜等
- **多端输出**: 飞书卡片 / 微信图文 / 纯文本

### 工作流程

```
数据获取 (AkShare)
    ↓
三分析师并行 (技术 / 基本面 / 情绪)
    ↓
多空辩论 (Bull vs Bear)
    ↓
交易信号生成
    ↓
风控审核
    ↓
报告输出 (飞书卡片)
```

### 使用示例

```python
from talent_link.agents.stock_analyst import StockAnalyst, FeishuCardRenderer

# 创建分析员
agent = StockAnalyst("000001", "平安银行")

# 执行分析
report = agent.analyze()

# 输出飞书卡片
card_json = FeishuCardRenderer.render(report, style="feishu")
```

## 🛠️ 开发指南

### 添加新的数字员工

1. 在 `src/talent_link/agents/` 创建新模块
2. 继承 `Agent` 基类（如有）
3. 实现 `analyze()` 方法
4. 在 `skills/` 添加专用技能

### 添加新的数据技能

1. 在 `src/talent_link/skills/` 创建新模块
2. 遵循 `*_wrapper.py` 命名规范
3. 添加类型注解和文档字符串

## 📄 许可证

MIT License

## 🙏 致谢

- [AkShare](https://github.com/akfamily/akshare) - A股数据源
- [OpenClaw](https://github.com/openclaw/openclaw) - Agent 运行时框架
