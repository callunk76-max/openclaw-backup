from tradingview_ta import TA_Handler, Interval, get_multiple_analysis
symbols = ["OANDA:EURUSD", "OANDA:GBPUSD"]
analysis = get_multiple_analysis(screener="forex", interval=Interval.INTERVAL_1_DAY, symbols=symbols)
for k, v in analysis.items():
    print(k, "Close:", v.indicators.get("close"), "High:", v.indicators.get("high"), "Low:", v.indicators.get("low"))
