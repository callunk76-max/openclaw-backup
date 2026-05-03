//+------------------------------------------------------------------+
//|                                          FX_Hedge_Scalper_EA.mq4 |
//|                                  Hedging Scalper - Reconstructed |
//|                   Based on Top-2 EA: Forex Hedge Scalper EA 2026 |
//+------------------------------------------------------------------+
#property copyright "FX Hedge Scalper EA - Reconstructed Logic"
#property version   "1.00"
#property strict

//============================================================
// STRATEGI INTI:
// 1. Scalping di M1/M5 — cari entry kecil-kecil cepat
// 2. Hedging otomatis — buka posisi opposite saat drawdown
// 3. Smart Drawdown Control — kurangi lot saat DD naik
// 4. Auto-recovery — pulihkan loss dengan hedge management
// 5. Low spread broker required
//============================================================

// --- INPUT PARAMETERS ---
input string ___STRATEGY___ = "==== STRATEGY SETTINGS ====";
input ENUM_TIMEFRAMES InpTradeTF = PERIOD_M1;         // Trading Timeframe (M1/M5)
input double   InpScalpTargetPips = 8.0;              // Scalp Target (pips)
input double   InpScalpSLPips = 15.0;                 // Scalp Stop Loss (pips)
input int      InpMaxTradesPerDirection = 3;           // Max trades per direction

input string ___HEDGE___ = "==== HEDGING SETTINGS ====";
input bool     InpHedgeEnabled = true;                // Enable Hedging
input double   InpHedgeTriggerPips = 20.0;            // Hedge trigger (pips loss)
input double   InpHedgeTPSame = 5.0;                  // Hedge take profit (pips)
input double   InpHedgeSL = 40.0;                     // Hedge stop loss (pips)

input string ___DDCONTROL___ = "==== DRAWDOWN CONTROL ====";
input bool     InpSmartDDControl = true;              // Smart Drawdown Control
input double   InpDDLevel1 = 5.0;                     // DD Level 1 (%) → reduce 20%
input double   InpDDLevel2 = 10.0;                    // DD Level 2 (%) → reduce 50%
input double   InpDDLevel3 = 15.0;                    // DD Level 3 (%) → stop trading
input double   InpDDRecoveryLevel = 3.0;              // Resume trading after DD < this %

input string ___MM___ = "==== MONEY MANAGEMENT ====";
input double   InpRiskPercent = 0.5;                  // Risk % per trade
input double   InpFixedLot = 0.0;                     // Fixed Lot (0 = use risk%)
input double   InpMaxLot = 5.0;                       // Max lot size

input string ___FILTERS___ = "==== FILTERS ====";
input int      InpMaxSpread = 15;                     // Max spread (points)
input double   InpMinVolume = 0.5;                    // Min volume ratio
input bool     InpTradeDuringNews = false;            // Trade during news?

input string ___ADV___ = "==== ADVANCED ====";
input int      InpMagicNumber = 20301;                // Magic Number
input string   InpComment = "HedgeScalper";
input bool     InpCloseOnProfitTarget = true;         // Close all at profit target
input double   InpDailyProfitTarget = 50.0;           // Daily profit target ($)

// --- GLOBAL VARIABLES ---
datetime g_lastBarTime = 0;
double g_currentDD = 0;
double g_dailyPL = 0;
datetime g_todayStart = 0;
double g_spread;
bool g_tradingPaused = false;

// Hedge tracking
int g_hedgeTicket = -1;
int g_mainTickets[10];
int g_mainCount = 0;

//+------------------------------------------------------------------+
//| Expert initialization                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   ResetHedgeTracking();
   
   // Start of day
   MqlDateTime dt;
   TimeCurrent(dt);
   g_todayStart = StringToTime(StringFormat("%d.%d.%d", dt.year, dt.mon, dt.day));
   
   Comment("FX Hedge Scalper EA Loaded\n",
           "Strategy: Hedging + Scalping\n",
           "Timeframe: M1/M5\n",
           "Magic: ", InpMagicNumber);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                          |
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
   // New day?
   MqlDateTime dt;
   TimeCurrent(dt);
   datetime today = StringToTime(String.Format("{0}.{1}.{2}", dt.year, dt.mon, dt.day));
   if(today != g_todayStart)
   {
      g_todayStart = today;
      g_dailyPL = 0;
      g_tradingPaused = false;
   }
   
   // New bar only
   if(Time[0] == g_lastBarTime) return;
   g_lastBarTime = Time[0];
   
   // Update
   g_spread = (Ask - Bid) / Point;
   UpdateDrawdown();
   UpdateDailyPL();
   CleanupMainTickets();
   
   // Check daily profit target
   if(InpCloseOnProfitTarget && g_dailyPL >= InpDailyProfitTarget)
   {
      CloseAllTrades();
      return;
   }
   
   // --- SMART DRAWDOWN CONTROL ---
   if(InpSmartDDControl)
   {
      if(g_currentDD >= InpDDLevel3)
      {
         if(!g_tradingPaused)
         {
            g_tradingPaused = true;
            CloseAllTrades();
            if(InpCloseOnProfitTarget == false)
               Print("DD > ", InpDDLevel3, "%. Trading paused.");
         }
         return;
      }
      else if(g_tradingPaused && g_currentDD <= InpDDRecoveryLevel)
      {
         g_tradingPaused = false;
         Print("DD recovered to ", g_currentDD, "%. Trading resumed.");
      }
      
      // DD level scaling
      if(g_currentDD >= InpDDLevel2)
      {
         // Heavy reduction - close half positions
         CloseHalfTrades();
         return;
      }
   }
   
   // --- SPREAD FILTER ---
   if(g_spread > InpMaxSpread * Point)
   {
      Comment("Spread too high: ", DoubleToStr(g_spread / Point, 1));
      return;
   }
   
   // --- MAIN STRATEGY ---
   // 1. Scan for scalp entry
   int signal = CheckScalpSignal();
   
   if(signal != 0 && g_mainCount < InpMaxTradesPerDirection)
   {
      double lot = CalculateLot();
      
      if(signal > 0)  // BUY signal
         OpenScalpTrade(OP_BUY, lot);
      else if(signal < 0)  // SELL signal
         OpenScalpTrade(OP_SELL, lot);
   }
   
   // 2. Hedging management (for losing positions)
   if(InpHedgeEnabled)
      ManageHedging();
   
   // Update comment
   UpdateComment();
}

//+------------------------------------------------------------------+
//| Check Scalp Signal using fast indicators                         |
//+------------------------------------------------------------------+
int CheckScalpSignal()
{
   // Multi-indicator confluence for scalping
   double fastMA_prev = iMA(NULL, InpTradeTF, 5, 0, MODE_EMA, PRICE_CLOSE, 2);
   double fastMA_curr = iMA(NULL, InpTradeTF, 5, 0, MODE_EMA, PRICE_CLOSE, 1);
   double slowMA = iMA(NULL, InpTradeTF, 21, 0, MODE_EMA, PRICE_CLOSE, 1);
   
   double rsi = iRSI(NULL, InpTradeTF, 7, PRICE_CLOSE, 1);
   double stochMain = iStochastic(NULL, InpTradeTF, 5, 3, 3, MODE_SMA, 0, MODE_MAIN, 1);
   double stochSignal = iStochastic(NULL, InpTradeTF, 5, 3, 3, MODE_SMA, 0, MODE_SIGNAL, 1);
   
   double macd = iMACD(NULL, InpTradeTF, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
   double macdSignal = iMACD(NULL, InpTradeTF, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 1);
   double macdHist = iMACD(NULL, InpTradeTF, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 2);
   
   double volumeMA = iVolume(NULL, InpTradeTF, 20, 1);
   double currentVol = Volume[1];
   bool volumeOK = (volumeMA > 0) ? (currentVol / volumeMA >= InpMinVolume) : true;
   if(!volumeOK) return 0;
   
   // --- BUY SIGNAL ---
   // EMA crossover + RSI oversold + MACD bullish + Stoch crossover
   if(fastMA_curr > fastMA_prev && Close[1] > slowMA &&
      rsi < 40 && rsi > 20 &&
      macd > macdSignal && macdHist < macd &&
      stochMain > stochSignal && stochMain < 30)
   {
      return 1;
   }
   
   // --- SELL SIGNAL ---
   if(fastMA_curr < fastMA_prev && Close[1] < slowMA &&
      rsi > 60 && rsi < 80 &&
      macd < macdSignal && macdHist > macd &&
      stochMain < stochSignal && stochMain > 70)
   {
      return -1;
   }
   
   return 0;
}

//+------------------------------------------------------------------+
//| Open scalp trade                                                 |
//+------------------------------------------------------------------+
void OpenScalpTrade(int type, double lot)
{
   double price = (type == OP_BUY) ? Ask : Bid;
   double sl, tp;
   
   int digit = (int)MarketInfo(Symbol(), MODE_DIGITS);
   double pipSize = (digit == 5 || digit == 3) ? 10 * Point : Point;
   
   if(type == OP_BUY)
   {
      sl = price - InpScalpSLPips * pipSize;
      tp = price + InpScalpTargetPips * pipSize;
   }
   else
   {
      sl = price + InpScalpSLPips * pipSize;
      tp = price - InpScalpTargetPips * pipSize;
   }
   
   sl = NormalizeDouble(sl, digit);
   tp = NormalizeDouble(tp, digit);
   price = NormalizeDouble(price, digit);
   
   int ticket = OrderSend(Symbol(), type, lot, price, 3, sl, tp,
                          InpComment, InpMagicNumber, 0,
                          (type == OP_BUY) ? clrGreen : clrRed);
   
   if(ticket > 0)
   {
      // Track ticket
      for(int i = 0; i < 10; i++)
      {
         if(g_mainTickets[i] == 0)
         {
            g_mainTickets[i] = ticket;
            g_mainCount++;
            break;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage Hedging — open hedge when scalp trades are losing         |
//+------------------------------------------------------------------+
void ManageHedging()
{
   // Check if any scalp trade is losing beyond trigger
   bool triggerHedge = false;
   double totalLossPips = 0;
   int lossDirection = 0;  // 1 = losing from BUY, -1 = losing from SELL
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() == OP_BUY && OrderProfit() < 0)
      {
         double lossPips = (OrderOpenPrice() - Bid) / Point;
         if(InpTradeTF == PERIOD_M1)
         {
            if(Digits() == 5 || Digits() == 3) lossPips /= 10;
         }
         if(lossPips >= InpHedgeTriggerPips)
         {
            triggerHedge = true;
            lossDirection = 1;
            totalLossPips += lossPips;
         }
      }
      else if(OrderType() == OP_SELL && OrderProfit() < 0)
      {
         double lossPips = (Ask - OrderOpenPrice()) / Point;
         if(InpTradeTF == PERIOD_M1)
         {
            if(Digits() == 5 || Digits() == 3) lossPips /= 10;
         }
         if(lossPips >= InpHedgeTriggerPips)
         {
            triggerHedge = true;
            lossDirection = -1;
            totalLossPips += lossPips;
         }
      }
   }
   
   if(!triggerHedge) return;
   
   // Check if hedge already exists
   bool hedgeExists = false;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderComment() == "Hedge")
      {
         hedgeExists = true;
         g_hedgeTicket = OrderTicket();
         break;
      }
   }
   
   if(hedgeExists)
   {
      // Check if hedge should be closed
      CheckHedgeClose();
      return;
   }
   
   // Open hedge position
   int hedgeType = (lossDirection == 1) ? OP_SELL : OP_BUY;
   double hedgeLot = 0;
   
   // Calculate hedge lot: enough to offset the loss
   double totalLossAmount = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderProfit() < 0)
         totalLossAmount += MathAbs(OrderProfit());
   }
   
   double pipValue = MarketInfo(Symbol(), MODE_TICKVALUE) * 10;
   if(pipValue > 0)
      hedgeLot = NormalizeDouble(totalLossAmount / (InpHedgeTPSame * pipValue), 2);
   
   if(hedgeLot < MarketInfo(Symbol(), MODE_MINLOT))
      hedgeLot = MarketInfo(Symbol(), MODE_MINLOT);
   if(hedgeLot > InpMaxLot)
      hedgeLot = InpMaxLot;
   
   double hedgePrice = (hedgeType == OP_BUY) ? Ask : Bid;
   double hedgeSL = (hedgeType == OP_BUY) ?
                     hedgePrice - InpHedgeSL * Point * 10 :
                     hedgePrice + InpHedgeSL * Point * 10;
   double hedgeTP = (hedgeType == OP_BUY) ?
                     hedgePrice + InpHedgeTPSame * Point * 10 :
                     hedgePrice - InpHedgeTPSame * Point * 10;
   
   int digit = (int)MarketInfo(Symbol(), MODE_DIGITS);
   hedgeSL = NormalizeDouble(hedgeSL, digit);
   hedgeTP = NormalizeDouble(hedgeTP, digit);
   hedgePrice = NormalizeDouble(hedgePrice, digit);
   
   int ticket = OrderSend(Symbol(), hedgeType, hedgeLot, hedgePrice, 3,
                          hedgeSL, hedgeTP, "Hedge", InpMagicNumber + 1, 0,
                          (hedgeType == OP_BUY) ? clrBlue : clrOrange);
   
   if(ticket > 0)
   {
      g_hedgeTicket = ticket;
      Print("Hedge opened: ", (hedgeType == OP_BUY) ? "BUY" : "SELL",
            " Lot: ", hedgeLot);
   }
}

//+------------------------------------------------------------------+
//| Check if hedge should be closed                                  |
//+------------------------------------------------------------------+
void CheckHedgeClose()
{
   if(g_hedgeTicket < 0) return;
   
   if(!OrderSelect(g_hedgeTicket, SELECT_BY_TICKET))
   {
      g_hedgeTicket = -1;
      return;
   }
   
   // Close hedge if the main losing positions are closed or profitable
   bool mainStillLosing = false;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderComment() == "Hedge") continue;
      
      if(OrderProfit() < -1.0)
      {
         mainStillLosing = true;
         break;
      }
   }
   
   // If hedge is in profit and main is no longer losing, close hedge
   if(!mainStillLosing && OrderProfit() > 0)
   {
      if(OrderClose(g_hedgeTicket, OrderLots(),
                    (OrderType() == OP_BUY) ? Bid : Ask, 3, clrWhite))
      {
         Print("Hedge closed in profit: $", OrderProfit());
         g_hedgeTicket = -1;
      }
   }
}

//+------------------------------------------------------------------+
//| Smart lot calculation with DD-based reduction                    |
//+------------------------------------------------------------------+
double CalculateLot()
{
   double lot;
   
   if(InpFixedLot > 0)
      lot = InpFixedLot;
   else
   {
      double riskAmount = AccountBalance() * InpRiskPercent / 100.0;
      double slPips = InpScalpSLPips;
      double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
      
      if(tickValue > 0 && slPips > 0)
         lot = riskAmount / (slPips * tickValue * 10);
      else
         lot = 0.01;
   }
   
   // Scale down based on drawdown (Smart DD Control)
   if(InpSmartDDControl)
   {
      if(g_currentDD >= InpDDLevel2)
         lot *= 0.5;   // Reduce 50%
      else if(g_currentDD >= InpDDLevel1)
         lot *= 0.8;   // Reduce 20%
   }
   
   // Normalize
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   double minLot = MarketInfo(Symbol(), MODE_MINLOT);
   if(lotStep > 0)
      lot = MathFloor(lot / lotStep) * lotStep;
   if(lot < minLot) lot = minLot;
   if(lot > InpMaxLot) lot = InpMaxLot;
   
   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| Update current drawdown %                                        |
//+------------------------------------------------------------------+
void UpdateDrawdown()
{
   if(AccountBalance() > 0)
   {
      double peakBalance = AccountBalance();
      
      // Find peak balance (simple: use current balance as baseline)
      for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
      {
         if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
         {
            if(OrderProfit() > 0)
               peakBalance += OrderProfit();
         }
      }
      
      double equity = AccountEquity();
      if(peakBalance > 0)
         g_currentDD = ((peakBalance - equity) / peakBalance) * 100.0;
      if(g_currentDD < 0) g_currentDD = 0;
   }
}

//+------------------------------------------------------------------+
//| Update daily profit/loss                                         |
//+------------------------------------------------------------------+
void UpdateDailyPL()
{
   g_dailyPL = 0;
   
   for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderCloseTime() >= g_todayStart)
         g_dailyPL += OrderProfit() + OrderSwap() + OrderCommission();
   }
   
   // Add floating P/L
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber && 
         OrderMagicNumber() != (InpMagicNumber + 1)) continue;
      g_dailyPL += OrderProfit() + OrderSwap() + OrderCommission();
   }
}

//+------------------------------------------------------------------+
//| Remove closed tickets from tracking array                        |
//+------------------------------------------------------------------+
void CleanupMainTickets()
{
   g_mainCount = 0;
   for(int i = 0; i < 10; i++)
   {
      if(g_mainTickets[i] != 0)
      {
         if(!OrderSelect(g_mainTickets[i], SELECT_BY_TICKET, MODE_TRADES))
            g_mainTickets[i] = 0;
         else
            g_mainCount++;
      }
   }
}

//+------------------------------------------------------------------+
//| Reset hedge tracking                                             |
//+------------------------------------------------------------------+
void ResetHedgeTracking()
{
   g_hedgeTicket = -1;
   g_mainCount = 0;
   for(int i = 0; i < 10; i++)
      g_mainTickets[i] = 0;
}

//+------------------------------------------------------------------+
//| Close all trades                                                 |
//+------------------------------------------------------------------+
void CloseAllTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber && 
         OrderMagicNumber() != (InpMagicNumber + 1)) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() <= OP_SELL)
      {
         OrderClose(OrderTicket(), OrderLots(),
                    (OrderType() == OP_BUY) ? Bid : Ask, 3, clrWhite);
      }
   }
   ResetHedgeTracking();
}

//+------------------------------------------------------------------+
//| Close half of all positions (DD Level 2)                         |
//+------------------------------------------------------------------+
void CloseHalfTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber && 
         OrderMagicNumber() != (InpMagicNumber + 1)) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() <= OP_SELL)
      {
         double halfLot = NormalizeDouble(OrderLots() / 2, 2);
         double minLot = MarketInfo(Symbol(), MODE_MINLOT);
         
         if(halfLot >= minLot)
         {
            OrderClose(OrderTicket(), halfLot,
                       (OrderType() == OP_BUY) ? Bid : Ask, 3, clrWhite);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Update chart comment                                             |
//+------------------------------------------------------------------+
void UpdateComment()
{
   string ddStatus;
   if(g_tradingPaused)
      ddStatus = "PAUSED ⛔";
   else if(g_currentDD >= InpDDLevel2)
      ddStatus = "CRITICAL 🔴";
   else if(g_currentDD >= InpDDLevel1)
      ddStatus = "WARNING 🟡";
   else
      ddStatus = "NORMAL 🟢";
   
   Comment("═══ FX HEDGE SCALPER EA ═══",
           "\nDrawdown: ", DoubleToStr(g_currentDD, 2), "% [", ddStatus, "]",
           "\nDaily P/L: $", DoubleToStr(g_dailyPL, 2),
           "\nSpread: ", DoubleToStr(g_spread / Point, 1),
           "\nActive Main: ", g_mainCount, "/", InpMaxTradesPerDirection,
           "\nHedge Active: ", (g_hedgeTicket > 0 ? "YES" : "NO"),
           "\nTrading: ", (g_tradingPaused ? "PAUSED" : "ACTIVE"));
}
//+------------------------------------------------------------------+
