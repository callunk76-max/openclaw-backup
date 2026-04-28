from tradingview_ta import TA_Handler, Interval
handler = TA_Handler(
    symbol="EURUSD",
    exchange="OANDA",
    screener="forex",
    interval=Interval.INTERVAL_1_DAY
)
analysis = handler.get_analysis()
print(analysis.indicators.keys())
print("High:", analysis.indicators.get("high"))
print("Low:", analysis.indicators.get("low"))
print("Close:", analysis.indicators.get("close"))
