# Hermes Stock Sentinel v1.0.0 使用笔记

更新时间：2026-04-22

## 1. 项目定位

Hermes Stock Sentinel v1.0.0 是一个单用户股票监控前端原型，核心目标是：

- 搜索股票
- 加入关注池
- 持续刷新盘中状态
- 由 Hermes 做风险监控和提醒
- 帮助用户优先处理高风险标的，保收益、降回撤、快响应

注意：

- 当前版本还是前端原型
- 不直接请求真实行情 API
- 页面里的实时数据来自内置样本 + 模拟 Tick
- Hermes 对话是规则驱动回复，不是外部大模型实时联网分析

## 2. 项目结构

核心文件：

- `index.html`：页面入口
- `styles.css`：界面样式
- `app.js`：前端状态管理、模拟行情、Hermes 风控与问答逻辑
- `scripts/start_local_server.sh`：启动本地静态服务
- `scripts/start_v1_dashboard.sh`：启动 v1.0.0 并自动打开浏览器
- `scripts/start_public_share.sh`：启动 Cloudflare 公网分享
- `scripts/query_public_share.sh`：查询本地/公网地址与运行状态
- `scripts/stop_public_share.sh`：停止公网分享
- `docs/V1_0_0_PRODUCT_SPEC.md`：产品定义
- `docs/V1_0_0_WORKFLOW.md`：工作流说明

## 3. 启动方式

### 本地启动

在项目目录执行：

```bash
cd /Users/starfeld/project/stock-realtime-dashboard
bash scripts/start_v1_dashboard.sh
```

或：

```bash
bash scripts/start_local_server.sh
```

默认地址：

- `http://127.0.0.1:8130`

补充：

- `start_v1_dashboard.sh` 会先调用 `start_local_server.sh`
- 然后尝试自动 `open` 本地页面
- 运行信息会写入 `.runtime/`

### 公网分享

```bash
cd /Users/starfeld/project/stock-realtime-dashboard
bash scripts/start_public_share.sh
```

查看当前地址：

```bash
bash scripts/query_public_share.sh
```

停止分享：

```bash
bash scripts/stop_public_share.sh
```

说明：

- 公网分享依赖 `cloudflared`
- 生成的是临时 `trycloudflare.com` 地址
- 地址通常会在重启后变化
- 只适合演示，不适合生产

## 4. v1.0.0 的实际使用流程

闭环是：

`搜索 -> 关注 -> 实时刷新 -> Hermes 监控 -> Hermes 提醒 -> 用户响应`

建议操作顺序：

1. 打开页面
2. 在左侧输入股票代码或名称
3. 点击“搜索并聚焦”
4. 点击“加入关注”
5. 在中间面板查看该股票的实时状态、信号、风控分和快讯
6. 在“关注池”里切换不同股票
7. 用 Hermes 对话框询问风险优先级和原因
8. 根据 Hermes 的风险提示做人工判断

## 5. 页面主要模块怎么用

### 5.1 搜索与关注

左侧支持：

- 搜索并聚焦
- 加入关注
- 移出关注
- 重置默认关注池

搜索逻辑：

- 支持按代码精确匹配
- 支持按名称包含匹配
- 如果不在内置股票池里，会弹窗提示“当前 v1.0.0 原型中未内置该股票”

### 5.2 监控模式

支持两个维度：

1. 市场范围
   - 美股
   - A股
   - 跨市场

2. Hermes 风控档位
   - 正常监控
   - 防守优先
   - 崩坏守卫

理解方式：

- 正常监控：常规盯盘
- 防守优先：更早提示回撤风险
- 崩坏守卫：更强调本金和利润保护，风险阈值更敏感

### 5.3 关注池

特点：

- 默认关注池：`AAPL`、`NVDA`、`TSLA`、`600519.SH`
- 关注池保存在浏览器 `localStorage`
- 键名：`stock-dashboard-v1-followed`
- 关闭页面后再次打开，关注池会保留
- 如果把关注池删空，逻辑上会回退到默认关注池

### 5.4 实时股票信息

当前选中股票会展示：

- 最新价
- 涨跌幅 / 涨跌额
- 开高低收
- 成交量 / 成交额
- 买一 / 卖一
- 点差
- 盘中简化走势

刷新机制：

- `app.js` 中使用 `setInterval(simulateStreamTick, 1800)`
- 即每约 1.8 秒刷新一次模拟 Tick

### 5.5 Hermes 风控镜头 / 排行 / 快讯

Hermes 会基于以下信息生成风控结果：

- 趋势
- 流动性
- 波动
- 收益保护
- 点差
- 量比
- 市场整体压力

页面上重点看：

- `Hermes 风险态势`
- `Protection Scores`
- `关注股排行与详情`
- `Hermes 快讯`
- `保收益检查单`
- `提醒规则面板`

实际使用时，优先看“关注股排行与详情”和“Hermes 快讯”。

## 6. Hermes 对话怎么用

右下角是 Hermes 对话控制台。

支持两种方式：

- 手动输入问题后点击“询问 Hermes”
- 点击“风险总览”自动填入预设问题

当前规则里较适合的问题类型：

- “当前最危险的股票是谁？”
- “为什么发这个提醒？”
- “当前关注哪些股票要优先处理？”
- “现在偏进攻还是防守？”
- “当前风险怎么样？”

内部判断逻辑大致是关键词匹配：

- 包含“危险 / 崩 / 风险” -> 返回当前最需要优先处理的股票
- 包含“为什么 / 原因” -> 解释当前选中股票为什么被打上某种风险标签
- 包含“关注 / 观察” -> 返回关注池数量和优先级靠前股票
- 其他情况 -> 返回当前聚焦股票的通用风险结论

所以要想得到更稳定的回答，问题最好带这些关键词。

## 7. v1.0.0 内置股票池

当前代码内置了 7 只股票：

美股：

- `AAPL`
- `NVDA`
- `TSLA`
- `PLTR`

A股：

- `600519.SH`
- `000858.SZ`
- `300750.SZ`

结论：

- v1.0.0 只能直接搜索这 7 只
- 其他股票当前不会真实查询，只会提示后续接入数据网关

## 8. 目前已确认可调用的方式

已验证：

- 项目目录存在：`/Users/starfeld/project/stock-realtime-dashboard`
- 本地访问地址为：`http://127.0.0.1:8130`
- 本地静态页面可以返回 `200 OK`
- `start_v1_dashboard.sh`、`start_local_server.sh`、`query_public_share.sh` 可正常调用
- 当前环境里 Cloudflare Tunnel 已在运行，可通过 `bash scripts/query_public_share.sh` 查看最新公网地址

## 9. 当前版本的边界

v1.0.0 能做的：

- 演示单用户盯盘工作台形态
- 演示关注池、风险优先级、快讯提醒、Hermes 问答
- 演示跨市场的观察视角

v1.0.0 还不能做的：

- 拉取真实实时行情
- 搜索任意股票
- 真实推送通知
- 真实账户、登录、多用户协作
- 真正基于外部行情 API 的风险模型

## 10. 如果后续我要继续接手这个项目，应该怎么用

我已经掌握的最短操作路径：

1. 进入目录：
   `cd /Users/starfeld/project/stock-realtime-dashboard`
2. 启动页面：
   `bash scripts/start_v1_dashboard.sh`
3. 查询状态：
   `bash scripts/query_public_share.sh`
4. 阅读核心逻辑：
   - `app.js`
   - `index.html`
   - `docs/V1_0_0_PRODUCT_SPEC.md`
   - `docs/V1_0_0_WORKFLOW.md`
5. 如果要扩版本：
   - 优先替换 `app.js` 里的内置样本与 `simulateStreamTick()`
   - 接入真实 Snapshot + WebSocket 数据源
   - 保留当前 Hermes 风控面板结构，逐步把模拟信号替换成真实信号

## 11. 给后续协作的备注

如果以后让我“调用这个 dashboard 里的股票信息”，我应该这样理解：

- v1.0.0 目前调用的是前端内置样本股票信息，不是真实行情接口
- 我可以读取、解释、修改这套原型中的股票样本、风控逻辑、问答逻辑和运行脚本
- 我也可以帮忙把它升级到真实数据接入版本

如果用户要的是“真实实时股票信息”，就不能只依赖 v1.0.0 原型，必须接入外部行情数据源。