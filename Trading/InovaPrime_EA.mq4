//+------------------------------------------------------------------+
//|                                              InovaPrime_EA.mq4   |
//|                                          Hybrid Order Block EA   |
//|                              Inspired by Inova Prime EA MT4 v2.1 |
//+------------------------------------------------------------------+
#property copyright "Inova Prime EA - Reconstructed Logic"
#property version   "2.10"
#property strict

// --- INPUT PARAMETERS ---
// Core Trading Setup
input string   ___Core___ = "==== CORE SETTINGS ====";
input ENUM_TIMEFRAMES InpTimeframe = PERIOD_H1;        // Trading Timeframe
input double   InpMinOrderBlockDist = 40.0;             // Min Order Block Distance (pips)
input double   InpATRFilter = 0.7;                      // ATR Volatility Filter

// Trend Management
input string   ___Trend___ = "==== TREND MANAGEMENT ====";
input bool     InpTrendManagement = true;               // Enable Trend Management
input ENUM_TIMEFRAMES InpTrendTF = PERIOD_MN1;          // Trend Timeframe (Monthly)
input bool     InpIgnoreCounterTrend = true;            // Ignore Counter Trend Trades

// Lot Management
input string   ___Lot___ = "==== LOT MANAGEMENT ====";
input double   InpFixedLot = 0.05;                      // Fixed Lot Size
input bool     InpUseAutoLot = false;                   // Use Auto Lot (Risk %)
input double   InpRiskPercent = 1.0;                    // Risk % per Trade (if AutoLot)
input double   InpLotMultiplier = 1.0;                  // Lot Multiplier Factor

// Martingale Recovery
input string   ___Martingale___ = "==== MARTINGALE RECOVERY ====";
input bool     InpMartingaleEnabled = true;             // Enable Martingale Recovery
input double   InpMartingaleMultiplier = 1.3;           // Martingale Lot Multiplier
input int      InpMaxMartingaleTrades = 15;             // Max Martingale Levels
input double   InpMartingaleCloseProfit = 5.0;          // Close All Profit Target ($)

// Risk Protection
input string   ___Risk___ = "==== RISK PROTECTION ====";
input int      InpMaxSpread = 30;                       // Max Spread (points)
input double   InpFloatingLossProtection = 10.0;        // Floating Loss Protection ($)
input bool     InpUseAutoSL = false;                    // Use Auto Stop Loss
input double   InpAutoSLPips = 200.0;                   // Auto Stop Loss (pips)

// Trade Execution
input string   ___Trade___ = "==== TRADE EXECUTION ====";
input bool     InpAllowHedging = true;                  // Allow Opposite Trades (Hedging)
input int      InpMagicNumber = 20241;                  // EA Magic Number
input string   InpTradeComment = "InovaPrime";          // Trade Comment

// --- GLOBAL VARIABLES ---
double g_atrValue;
double g_spread;
double g_trendMA;
int g_martingaleCount = 0;
double g_martingaleBaseLot = 0;
datetime g_lastBarTime = 0;
double g_orderBlockHigh = 0;
double g_orderBlockLow = 0;
bool g_orderBlockBullish = false;
bool g_orderBlockBearish = false;
int g_orderBlockBar = -1;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   if(InpTimeframe == PERIOD_CURRENT) InpTimeframe = PERIOD_H1;
   
   Comment("Inova Prime EA v2.1 Loaded\n",
           "Magic Number: ", InpMagicNumber, "\n",
           "Timeframe: H1\n",
           "Trend Filter: Monthly\n",
           "Martingale: ", (InpMartingaleEnabled ? "Enabled" : "Disabled"), "\n",
           "Initial Lot: ", DoubleToStr(InpFixedLot, 2));
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
int OnDeinit()
{
   Comment("");
   return(0);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Run on new bar only
   if(Time[0] == g_lastBarTime) return;
   g_lastBarTime = Time[0];
   
   // Update ATR, Spread
   g_atrValue = iATR(NULL, 0, 14, 1);
   g_spread = (Ask - Bid) / Point;
   
   // --- CHECKS ---
   // 1. Spread Filter
   if(g_spread > InpMaxSpread * Point)
   {
      Comment("Spread too high: ", DoubleToStr(g_spread / Point, 1));
      return;
   }
   
   // 2. ATR Filter (volatility must be sufficient)
   double atrPips = g_atrValue / Point;
   if(atrPips < InpATRFilter * 10)
   {
      Comment("ATR too low: ", DoubleToStr(atrPips, 1));
      return;
   }
   
   // 3. Trend Filter (Monthly MA)
   double monthlyMA = iMA(NULL, PERIOD_MN1, 20, 0, MODE_SMA, PRICE_CLOSE, 1);
   bool isBullishTrend = (Close[0] > monthlyMA);
   
   // --- DETECT ORDER BLOCKS ---
   DetectOrderBlocks();
   
   // --- TREND DIRECTION CHECK ---
   int trendDirection = 0; // 1 = Bullish, -1 = Bearish
   if(InpTrendManagement)
   {
      if(isBullishTrend)
         trendDirection = 1;
      else
         trendDirection = -1;
   }
   
   // --- MARTINGALE RECOVERY: Check existing losing positions ---
   if(InpMartingaleEnabled)
      ManageMartingale();
   
   // --- FLOATING LOSS PROTECTION ---
   if(InpFloatingLossProtection > 0)
      CheckFloatingLoss();
   
   // --- ENTRY SIGNALS ---
   if(g_orderBlockBullish && (!InpIgnoreCounterTrend || trendDirection != -1))
   {
      if(!IsPositionExists(OP_BUY))
         EnterTrade(OP_BUY);
   }
   else if(g_orderBlockBearish && (!InpIgnoreCounterTrend || trendDirection != 1))
   {
      if(!IsPositionExists(OP_SELL))
         EnterTrade(OP_SELL);
   }
   
   // --- UPDATE COMMENT ---
   string trendStr = isBullishTrend ? "BULLISH" : "BEARISH";
   Comment("Inova Prime EA | Trend: ", trendStr,
           "\nATR: ", DoubleToStr(atrPips, 1), " pips",
           "\nSpread: ", DoubleToStr(g_spread / Point, 1),
           "\nMartingale Level: ", g_martingaleCount,
           "\nOrderBlock: ", (g_orderBlockBullish ? "BUY" : (g_orderBlockBearish ? "SELL" : "NONE")));
}

//+------------------------------------------------------------------+
//| Detect Order Blocks (Supply & Demand Zones)                      |
//+------------------------------------------------------------------+
void DetectOrderBlocks()
{
   g_orderBlockBullish = false;
   g_orderBlockBearish = false;
   g_orderBlockHigh = 0;
   g_orderBlockLow = 0;
   
   // Scan last 50 bars for impulse moves
   for(int i = 3; i < 50; i++)
   {
      // Bullish Order Block: big green candle followed by continuation
      double candleBody = MathAbs(Close[i] - Open[i]);
      double candleRange = High[i] - Low[i];
      double prevBody = MathAbs(Close[i+1] - Open[i+1]);
      
      // Strong impulse (bullish): body > 60% of range, and larger than previous
      if(Close[i] > Open[i] && 
         candleBody > candleRange * 0.6 &&
         candleBody > prevBody * 1.5 &&
         candleRange > InpMinOrderBlockDist * Point)
      {
         // Check if price retraced back near this candle's low
         double retraceHigh = High[i];
         double retraceLow = Low[i];
         
         for(int j = i-1; j >= 1; j--)
         {
            // If price came back to the zone
            if(Low[j] <= High[i] && Low[j] >= Low[i] - (candleRange * 0.3))
            {
               g_orderBlockBullish = true;
               g_orderBlockHigh = High[i];
               g_orderBlockLow = Low[i];
               g_orderBlockBar = i;
               return;
            }
         }
      }
      
      // Bearish Order Block: big red candle followed by continuation  
      if(Close[i] < Open[i] &&
         candleBody > candleRange * 0.6 &&
         candleBody > prevBody * 1.5 &&
         candleRange > InpMinOrderBlockDist * Point)
      {
         // Check if price retraced back near this candle's high
         for(int j = i-1; j >= 1; j--)
         {
            if(High[j] >= Low[i] && High[j] <= High[i] + (candleRange * 0.3))
            {
               g_orderBlockBearish = true;
               g_orderBlockHigh = High[i];
               g_orderBlockLow = Low[i];
               g_orderBlockBar = i;
               return;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size                                               |
//+------------------------------------------------------------------+
double CalculateLotSize(int tradeType)
{
   double lot = InpFixedLot;
   
   if(InpUseAutoLot)
   {
      double riskAmount = AccountBalance() * InpRiskPercent / 100.0;
      double stopLossPips = InpAutoSLPips;
      double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
      
      if(tickValue > 0 && stopLossPips > 0)
      {
         double riskLot = riskAmount / (stopLossPips * tickValue);
         lot = NormalizeDouble(riskLot, 2);
      }
   }
   
   // Apply martingale multiplier
   if(InpMartingaleEnabled && g_martingaleCount > 0)
      lot *= MathPow(InpMartingaleMultiplier, g_martingaleCount);
   
   // Min/Max check
   double minLot = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
   
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;
   
   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| Enter Trade                                                      |
//+------------------------------------------------------------------+
void EnterTrade(int tradeType)
{
   double price = (tradeType == OP_BUY) ? Ask : Bid;
   double stopLoss = 0;
   double takeProfit = 0;
   double lot = CalculateLotSize(tradeType);
   
   // Calculate SL & TP based on Order Block
   if(tradeType == OP_BUY && g_orderBlockLow > 0)
   {
      stopLoss = g_orderBlockLow - (10 * Point); // Slightly below OB
      double riskPips = (price - stopLoss) / Point;
      takeProfit = price + (riskPips * 2.0 * Point); // RR 1:2
   }
   else if(tradeType == OP_SELL && g_orderBlockHigh > 0)
   {
      stopLoss = g_orderBlockHigh + (10 * Point); // Slightly above OB
      double riskPips = (stopLoss - price) / Point;
      takeProfit = price - (riskPips * 2.0 * Point); // RR 1:2
   }
   
   // Apply auto SL as fallback
   if(stopLoss == 0 && InpUseAutoSL)
   {
      if(tradeType == OP_BUY)
         stopLoss = price - InpAutoSLPips * Point;
      else
         stopLoss = price + InpAutoSLPips * Point;
   }
   
   // Normalize prices
   int digit = (int)MarketInfo(Symbol(), MODE_DIGITS);
   stopLoss = NormalizeDouble(stopLoss, digit);
   takeProfit = NormalizeDouble(takeProfit, digit);
   price = NormalizeDouble(price, digit);
   
   // Send order
   int ticket = OrderSend(Symbol(), tradeType, lot, price, 3, 
                          stopLoss, takeProfit, 
                          InpTradeComment, InpMagicNumber, 0, 
                          (tradeType == OP_BUY) ? clrGreen : clrRed);
   
   if(ticket > 0)
   {
      g_martingaleBaseLot = lot;
      if(g_martingaleCount > 0) g_martingaleCount = 0;
   }
}

//+------------------------------------------------------------------+
//| Manage Martingale Recovery                                       |
//+------------------------------------------------------------------+
void ManageMartingale()
{
   int lossCount = 0;
   double totalLoss = 0;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderProfit() < 0)
      {
         lossCount++;
         totalLoss += MathAbs(OrderProfit());
      }
   }
   
   g_martingaleCount = lossCount;
   
   // If we hit max martingale levels, close all
   if(g_martingaleCount >= InpMaxMartingaleTrades)
   {
      CloseAllOrders();
      g_martingaleCount = 0;
   }
   
   // If total floating profit hits target, close all
   double totalProfit = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      totalProfit += OrderProfit();
   }
   
   if(totalProfit >= InpMartingaleCloseProfit)
      CloseAllOrders();
}

//+------------------------------------------------------------------+
//| Check Floating Loss Protection                                   |
//+------------------------------------------------------------------+
void CheckFloatingLoss()
{
   double totalFloatingLoss = 0;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderProfit() < 0)
         totalFloatingLoss += MathAbs(OrderProfit());
   }
   
   if(totalFloatingLoss >= InpFloatingLossProtection)
      CloseAllOrders();
}

//+------------------------------------------------------------------+
//| Check if position exists for given type                          |
//+------------------------------------------------------------------+
bool IsPositionExists(int tradeType)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderType() == tradeType) return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Close all orders for this symbol/magic                           |
//+------------------------------------------------------------------+
void CloseAllOrders()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() <= OP_SELL)
      {
         if(!OrderClose(OrderTicket(), OrderLots(), 
                        (OrderType() == OP_BUY) ? Bid : Ask, 3, clrWhite))
         {
            Print("Failed to close order #", OrderTicket());
         }
      }
   }
}
//+------------------------------------------------------------------+
