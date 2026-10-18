# Hertzflow Signal 跟单

监听 Telegram 频道 `@hertzflowcrypto`。只处理**同时带有明确多空方向、标的、止盈、止损**的帖子，解析后按这些点位填 Binance USDT-M 永续单。其它消息全部丢掉。

默认 `DRY_RUN=true`，只打日志，不下真单。

## 跑起来

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

1. Telegram：打开 https://my.telegram.org 申请 `api_id` / `api_hash`，填进 `.env`。第一次运行会要求手机号验证码，生成 `data/hertzflow.session`，以后不用再登。
2. 频道：账号必须已经加入 `@hertzflowcrypto`。
3. 先空跑：

```bash
python -m hertzflow_signal.main
```

测解析：

```bash
pytest
```

## 下真单

`.env` 里填 Binance API（建议先 `BINANCE_TESTNET=true`），然后：

```
DRY_RUN=false
LIVE=true
```

`POSITION_USDT` 是每笔名义本金，`LEVERAGE` 默认 1。入场走市价，不挂帖子里的「当前价」（发出时已经过时）。止盈写 `Trailing` 时用 Binance 追踪止盈，否则用帖内止盈价。

同一标的已有仓位会跳过，处理过的消息 id 存在 `data/state.json`。

## Docker

```bash
docker compose up --build
```

session 文件挂在 `./data`。
