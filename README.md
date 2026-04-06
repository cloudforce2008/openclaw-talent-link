# OpenClaw Talent Link

> 基于 OpenClaw 生态的数字人才市场平台 — 让每一个配置精良的 Agent 都能成为"数字员工"，通过标准化接口实现能力的商业化变现。

## 🎯 项目愿景

**"雇佣数字员工的第一站"** —— 一个连接"会养 Agent 的人"和"需要 Agent 能力的人"的平台。

## 📦 核心数字员工

| 员工 | 定位 | 阶段 |
| :--- | :--- | :--- |
| 📈 股票分析员 | A 股实时行情、多源数据交叉验证、7-Agent 深度分析 | MVP |
| 🛡️ 保险经纪人助理 | 跨学科 RAG、家庭画像、主动关系维护 | 规划中 |
| ✍️ 内容创作者助手 | 风格指纹克隆、多平台自适应重构 | 规划中 |

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

# 运行股票分析员测试
python -m src.talent_link.agents.stock_analyst
```

## 📁 目录结构

```
openclaw-talent-link/
├── src/talent_link/
│   ├── agents/          # 数字员工核心逻辑
│   ├── skills/          # 可复用技能模块
│   ├── platform/        # 平台基建
│   └── memory/          # 记忆与进化系统
├── tests/               # 测试用例
├── docs/                # 文档
└── scripts/             # 工具脚本
```

## 📄 许可证

MIT License
