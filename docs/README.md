# OpenTrade 中文文档

[English](../README.md) | [中文](./README.md)

OpenTrade 是一个面向团队内部使用的 AI 加密货币量化研究与模拟交易平台，前端使用 `Vue 3`，后端使用 `FastAPI`。系统支持配置多个 AI 模型，在相同市场数据输入下进行周期性决策、记录结构化输出，并在统一仪表盘中对比不同模型的持仓、订单与收益表现。

## 首页截图

![OpenTrade 首页截图](./view.png)

## 项目定位

- 面向内部研究和策略验证
- 当前以 `BTC`、`ETH`、`SOL` 三个现货交易对为主
- 当前执行模式为模拟交易
- 架构上保留扩展到真实交易接口的空间

## 主要功能

### 1. 多模型配置

可以为不同 AI 模型分别配置：

- `API Key`
- `Base URL`
- `Model`
- `Provider`
- `temperature`
- `max_tokens`
- `timeout_seconds`
- 是否参与自动策略

系统会对密钥进行加密存储，前端仅展示脱敏后的内容。

### 2. 实时行情与指标

- 通过 Binance WebSocket 推送实时价格
- 通过 Binance REST 获取历史 K 线
- 计算技术指标，作为模型决策输入的一部分
- 在首页展示 `BTC`、`ETH`、`SOL` 的最新行情

### 3. 周期性 AI 决策

每次策略轮询时，系统会向启用中的模型传递：

- 当前市场快照
- 历史 K 线
- 技术指标
- 最近决策记录
- 当前持仓状态
- 组合资金与净值情况

模型必须返回严格的 JSON 结构；如果返回为空、格式错误或接口调用失败，系统会自动回退为 `HOLD`。

### 4. 模拟交易执行

每个模型拥有独立的纸面账户，系统会分别记录：

- 现金余额
- 持仓
- 平均持仓成本
- 已实现收益和未实现收益
- 订单记录
- NAV 历史曲线

当前支持多仓位持仓，并会模拟手续费与滑点。

### 5. 可视化仪表盘

首页当前主要展示：

- 三个交易标的的实时价格
- 不同模型的收益率曲线
- 当前组合概览
- 持仓情况
- 最近订单
- 最近 AI 决策日志

其中收益率曲线目前按以下公式计算：

```text
(NAV - initial_capital) / initial_capital
```

## 目录结构

- `frontend/`：前端页面、组件、状态管理与图表
- `backend/`：接口服务、调度器、市场数据、AI 路由与模拟交易执行
- `docs/`：项目文档与截图资源
- `.env`：本地环境配置

## 本地启动

### 后端

如果你使用 Conda 环境：

```bash
cd backend
conda activate myenv
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`

## 关键配置

项目根目录下的 `.env` 可用于配置核心运行参数，例如：

```env
APP_NAME=OpenTrade
APP_TIMEZONE=Asia/Shanghai
DATABASE_URL=sqlite:///./data/opentrade.db
INITIAL_CASH_USDT=10000
DECISION_INTERVAL_SECONDS=300
BINANCE_WS_URL=wss://stream.binance.com:9443/stream
BINANCE_REST_URL=https://api.binance.com
```

## 当前限制

- 当前仅支持现货模拟交易
- 当前仅跟踪 `BTC`、`ETH`、`SOL`
- 主要用于研究与回测展示，不适合作为生产级自动交易系统
- 收益率曲线与策略表现仍在持续迭代中
