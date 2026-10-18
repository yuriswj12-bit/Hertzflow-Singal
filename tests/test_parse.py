from hertzflow_signal.parse import parse_signal

SAMPLE = """🐻 Crime Token Crash Short / 妖币崩盘做空

标的  CYSUSDT
当前价 Entry  0.77430    24H: +26.53%
OI  $15.5M    1H: +4.2%
Funding  8H +0.031%
止盈 TP  Trailing
止损 SL  0.89044    +15.0%
触发理由 Trigger  短时极端拉升后大幅回落 (Crime Token 出货特征)
"""

LONG_SAMPLE = """📈 Pump Long / 做多

Asset: BTCUSDT
Entry: 64000
TP: 66000
SL: 63000
"""

AD = """HertzFlow 平台宣传：BTC 永续最高 200x，自托管，零滑点。欢迎来玩。"""

INCOMPLETE = """🐻 Crime Token Crash Short / 妖币崩盘做空
标的  CYSUSDT
当前价  0.77430
"""


def test_sample_short_trailing():
    s = parse_signal(SAMPLE)
    assert s is not None
    assert s.side == "SHORT"
    assert s.symbol == "CYSUSDT"
    assert s.stop_loss == 0.89044
    assert s.trailing is True
    assert s.take_profit is None
    assert s.entry == 0.77430


def test_long_fixed_tp():
    s = parse_signal(LONG_SAMPLE)
    assert s is not None
    assert s.side == "LONG"
    assert s.symbol == "BTCUSDT"
    assert s.take_profit == 66000
    assert s.stop_loss == 63000
    assert s.trailing is False


def test_reject_ad():
    assert parse_signal(AD) is None


def test_reject_incomplete_no_sl_tp():
    assert parse_signal(INCOMPLETE) is None
