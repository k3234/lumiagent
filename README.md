# LumiAgent

> 为老旧设备而生的 AI 编程调度器

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 一句话定位

让没有 GPU 的老旧电脑，也能平等地获得 AI 编程辅助。

---

## 核心理念

- **算力平权** — 不再因为没有高端显卡就被 AI 时代抛弃
- **休息机制** — 任务完成后主动卸载模型，让设备喘口气
- **极简主义** — 80 行代码，每行都有中文注释，初学者也能看懂

---

## 快速开始

```bash
# 1. 确保你的电脑已安装并启动 Ollama
# 在终端中运行：ollama serve

# 2. 拉取一个本地模型（推荐这个，比较小）
ollama pull deepseek-r1:1.5b

# 3. 克隆项目
git clone https://github.com/k3234/lumiagent.git
cd lumiagent

# 4. 安装依赖（只需要 requests）
pip install -r requirements.txt

# 5. ⚠️ 修改 agent_core.py 第 11-12 行的配置
#     第 11 行：将 Ollama 地址改为你的地址（默认 http://localhost:11434）
#     第 12 行：将模型名改为你已拉取的模型（如 qwen2.5:7b）

# 6. 启动 Agent
python agent_core.py
```

---

## 使用说明

| 命令 | 说明 |
|------|------|
| 直接输入问题 | 获取 AI 回答 |
| `/help` | 查看帮助信息 |
| `exit` / `quit` / `退出` | 退出程序 |

---

## 工作原理

```
┌──────────────────────────────────────┐
│           LumiAgent 调度流程          │
├──────────────────────────────────────┤
│  1. 接收用户问题                      │
│  2. 调用本地 Ollama 模型              │
│  3. 返回 AI 回答                      │
│  4. 进入 30 秒休眠 ⏱                 │
│  5. 卸载模型，释放内存                 │
│  6. 等待下一个问题                    │
└──────────────────────────────────────┘
```

**为什么需要休息机制？**

老旧设备的内存有限。模型一旦加载会一直占用 RAM。LumiAgent 在每次回答后主动等待 30 秒，让操作系统有机会卸载模型释放内存——这才是"老设备也能用"的关键。

---

## 开发者故事

我是 Kai，一名高一学生。

我没有高端显卡，只有一台普通配置的电脑。但我也不想被 AI 时代甩下。

所以我用最直接的方式——调用 Ollama API，写了这 80 行 Python——做出了一套给老旧设备用的 AI 编程助手。

这不只是一个工具，它是我证明 "没有好设备，也能做事情" 的方式。

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 运行时 | Python 3.8+ |
| 模型调用 | Ollama API (`requests`) |
| 模型 | `deepseek-r1:1.5b`（默认，可替换为任意 Ollama 模型） |
| 部署方式 | 纯本地，无需联网 |

---

## 项目结构

```
lumiagent/
├── agent_core.py    # 核心代码（80行，含中文注释）
├── requirements.txt # 依赖列表
├── .gitignore       # Git 忽略文件
├── DEV_LOG.md       # 开发日志
├── V2_ROADMAP.md    # V2 未来规划
└── README.md        # 本文件
```

---

## V2 未来规划

详见 [V2_ROADMAP.md](V2_ROADMAP.md)（含 TRAE AI 创造力大赛参赛计划）

| 方向 | 说明 |
|:---|:---|
| 内容自检 | 检测模型回答中的技术错误，提醒用户保持警惕 |
| 系统提示词 | 切换到 chat 端点 + 极简提示词模板 |
| 动态休眠 | 根据任务复杂度自动调整休眠时长 |
| HTTP API | 预留 RESTful 接口，支持其他工具调用 |
| 多模型支持 | 设计统一适配器，支持模型切换和对比 |

---

## License

MIT License
