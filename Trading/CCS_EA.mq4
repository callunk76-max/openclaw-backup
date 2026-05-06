//+------------------------------------------------------------------+
//|                                            CCS_EA.mq4             |
//|                 Callunk Confluence System — EA dengan Trading      |
//|                                        Callunk & Cuy              |
//+------------------------------------------------------------------+
#property copyright "Callunk & Cuy"
#property version   "1.00"
#property strict
#property description "CCS EA — Panel Info + Trading Button"
#property description "Attach ke chart H1 atau M15. AutoTrading: ON utk auto"

// ─── INPUT PARAMETERS ─────────────────────────────────────────────
input string   s1_            = "─── EMA GATES (H1) ───";
input int      EMA20_Period   = 20;
input int      EMA50_Period   = 50;
input int      EMA100_Period  = 100;
input int      EMA200_Period  = 200;
input ENUM_MA_METHOD EMA_Method = MODE_EMA;

input string   s2_            = "─── BOLLINGER BANDS (M15) ───";
input int      BB_Period      = 20;
input double   BB_Deviation   = 2.0;
input int      BB_Shift       = 0;

input string   s3_            = "─── RSI (M15) ───";
input int      RSI_Period     = 14;
input double   RSI_Oversold   = 30.0;
input double   RSI_Overbought = 70.0;

input string   s4_            = "─── ATR (M15) ───";
input int      ATR_Period     = 14;
input double   ATR_SL_Mult    = 1.5;
input double   ATR_TP_Mult    = 2.0;

input string   s5_            = "─── SnR SWING POINTS ───";
input int      SnR_BarsLeft   = 3;
input int      SnR_BarsRight  = 3;
input int      SnR_MaxLevels  = 20;

input string   s6_            = "─── TRADING ───";
input double   Lot_Size       = 0.01;
input int      Slippage       = 10;
input int      Magic_Number   = 20260506;
input double   Max_Spread_Pips = 20.0;  // Skip order kalo spread > ini
input bool     Allow_Multiple  = false; // false = cuma 1 posisi per arah
input bool     Auto_Trade      = false; // true = ikut signal otomatis

input string   s7_            = "─── DISPLAY ───";
input int      Panel_X         = 15;
input int      Panel_Y         = 25;
input color    Panel_BG_Color  = clrBlack;

// ─── GLOBAL VARIABLES ─────────────────────────────────────────────
string INDICATOR_NAME = "CCS";
bool   bbLowerTouch    = false;
bool   bbUpperTouch    = false;
bool   atrNaik         = false;
bool   atrTurun        = false;
int    gateBull        = 0;
int    gateBear        = 0;
int    panelHeight     = 0;
int    signal          = 0;

// ─── INIT ─────────────────────────────────────────────────────────
int OnInit() {
   Comment("CCS EA v1.00 — ", TerminalCompany(), " | ", AccountServer());
   return INIT_SUCCEEDED;
}

// ─── DEINIT ───────────────────────────────────────────────────────
void OnDeinit(const int reason) {
   Comment("");
   DeleteAllObjects();
}

// ─── ON TICK (EA entry point) ─────────────────────────────────────
datetime lastBarTime = 0;

void OnTick() {
   // Hanya proses di candle baru
   datetime currentBarTime = iTime(NULL, 0, 0);
   if(currentBarTime == lastBarTime) return;
   lastBarTime = currentBarTime;
   
   // Spread check — print warning kalo spread lebar
   double spreadPips = (Ask - Bid) / Point;
   if(spreadPips > Max_Spread_Pips) Print("WARNING: Spread ", spreadPips, " pips > Max ", Max_Spread_Pips);
   
   // Kalkulasi ulang
   ResetState();
   FetchH1Data();
   FetchM15Data();
   CalculateSnRLevels();
   signal = EvaluateSignal();
   
   // Update panel + tombol
   DrawPanel();
   DrawButtons();
   
   // Auto trade (optional)
   if(Auto_Trade && spreadPips <= Max_Spread_Pips) {
      int posCount = CountPositions();
      if(signal == 2 && !HasBuy())  ExecuteBuy();
      if(signal == -2 && !HasSell()) ExecuteSell();
      if(signal <= 0 && posCount > 0) CloseAllPositions();
   }
}

// ─── RESET STATE ──────────────────────────────────────────────────
void ResetState() {
   h1_close  = 0;
   ema20_h1  = 0; ema50_h1  = 0; ema100_h1 = 0; ema200_h1 = 0;
   m15_close = 0; m15_high  = 0; m15_low   = 0;
   bb_upper  = 0; bb_middle = 0; bb_lower  = 0;
   rsi_value = 0; rsi_prev  = 0;
   atr_value = 0; atr_10bars_ago = 0;
   bbLowerTouch = false; bbUpperTouch = false;
   atrNaik = false; atrTurun = false;
   gateBull = 0; gateBear = 0;
   signal = 0;
   nearestSupport = 0; nearestResist = 0;
   nearestSupportDist = 999999; nearestResistDist = 999999;
}

// ─── H1 DATA ──────────────────────────────────────────────────────
double ema20_h1, ema50_h1, ema100_h1, ema200_h1;
double h1_close;

void FetchH1Data() {
   int shift_h1 = iBarShift(NULL, PERIOD_H1, TimeCurrent());
   if(shift_h1 < 0) {
      h1_close = 0; ema20_h1 = 0; ema50_h1 = 0; ema100_h1 = 0; ema200_h1 = 0;
      return;
   }
   h1_close   = iClose(NULL, PERIOD_H1, shift_h1);
   ema20_h1   = iMA(NULL, PERIOD_H1, EMA20_Period,  0, EMA_Method, PRICE_CLOSE, shift_h1);
   ema50_h1   = iMA(NULL, PERIOD_H1, EMA50_Period,  0, EMA_Method, PRICE_CLOSE, shift_h1);
   ema100_h1  = iMA(NULL, PERIOD_H1, EMA100_Period, 0, EMA_Method, PRICE_CLOSE, shift_h1);
   ema200_h1  = iMA(NULL, PERIOD_H1, EMA200_Period, 0, EMA_Method, PRICE_CLOSE, shift_h1);
}

// ─── M15 DATA ─────────────────────────────────────────────────────
double bb_upper, bb_middle, bb_lower;
double rsi_value, rsi_prev;
double atr_value, atr_10bars_ago;
double m15_close, m15_high, m15_low;

void FetchM15Data() {
   int shift_m15 = iBarShift(NULL, PERIOD_M15, TimeCurrent());
   if(shift_m15 < 0) {
      m15_close = 0; m15_high = 0; m15_low = 0;
      bb_upper = 0; bb_middle = 0; bb_lower = 0;
      rsi_value = 0; rsi_prev = 0;
      atr_value = 0; atr_10bars_ago = 0;
      return;
   }
   m15_close  = iClose(NULL, PERIOD_M15, shift_m15);
   m15_high   = iHigh(NULL, PERIOD_M15, shift_m15);
   m15_low    = iLow(NULL, PERIOD_M15, shift_m15);
   bb_upper   = iBands(NULL, PERIOD_M15, BB_Period, BB_Deviation, BB_Shift, PRICE_CLOSE, MODE_UPPER,  shift_m15);
   bb_middle  = iBands(NULL, PERIOD_M15, BB_Period, BB_Deviation, BB_Shift, PRICE_CLOSE, MODE_MAIN,   shift_m15);
   bb_lower   = iBands(NULL, PERIOD_M15, BB_Period, BB_Deviation, BB_Shift, PRICE_CLOSE, MODE_LOWER,  shift_m15);
   rsi_value  = iRSI(NULL, PERIOD_M15, RSI_Period, PRICE_CLOSE, shift_m15);
   rsi_prev   = iRSI(NULL, PERIOD_M15, RSI_Period, PRICE_CLOSE, shift_m15 + 1);
   atr_value       = iATR(NULL, PERIOD_M15, ATR_Period, shift_m15);
   atr_10bars_ago  = iATR(NULL, PERIOD_M15, ATR_Period, shift_m15 + 10);
}

// ─── SnR LEVELS ───────────────────────────────────────────────────
struct SnRLevel {
   double price;
   bool   isSupport;
   int    strength;
};

SnRLevel snrLevels[];
int snrCount = 0;

void CalculateSnRLevels() {
   ArrayResize(snrLevels, SnR_MaxLevels);
   snrCount = 0;
   
   int bars = MathMin(500, iBars(NULL, PERIOD_H1));
   if(bars < SnR_BarsLeft + SnR_BarsRight + 1) return;
   
   for(int i = SnR_BarsLeft; i < bars - SnR_BarsRight; i++) {
      if(snrCount >= SnR_MaxLevels) break;
      
      double swingHigh = iHigh(NULL, PERIOD_H1, i);
      double swingLow  = iLow(NULL, PERIOD_H1, i);
      bool isSH = true, isSL = true;
      
      for(int j = 1; j <= SnR_BarsLeft; j++) {
         if(swingHigh <= iHigh(NULL, PERIOD_H1, i+j)) isSH = false;
         if(swingLow  >= iLow(NULL, PERIOD_H1, i+j))  isSL = false;
      }
      for(int j = 1; j <= SnR_BarsRight; j++) {
         if(swingHigh <= iHigh(NULL, PERIOD_H1, i-j)) isSH = false;
         if(swingLow  >= iLow(NULL, PERIOD_H1, i-j))  isSL = false;
      }
      
      if(isSH == isSL) continue;
      
      if(isSH) { snrLevels[snrCount].price = swingHigh; snrLevels[snrCount].isSupport = false; snrLevels[snrCount].strength = 2; snrCount++; }
      if(isSL) { snrLevels[snrCount].price = swingLow;  snrLevels[snrCount].isSupport = true;  snrLevels[snrCount].strength = 2; snrCount++; }
   }
}

double nearestSupport = 0, nearestResist = 0;
double nearestSupportDist = 0, nearestResistDist = 0;

void FindNearestSnR(double price) {
   nearestSupport = 0; nearestResist = 0;
   nearestSupportDist = 999999; nearestResistDist = 999999;
   for(int i = 0; i < snrCount; i++) {
      double d = MathAbs(snrLevels[i].price - price);
      if(snrLevels[i].isSupport && price > snrLevels[i].price && d < nearestSupportDist) { nearestSupport = snrLevels[i].price; nearestSupportDist = d; }
      if(!snrLevels[i].isSupport && price < snrLevels[i].price && d < nearestResistDist)  { nearestResist  = snrLevels[i].price; nearestResistDist  = d; }
   }
}

// ─── SIGNAL EVALUATION ───────────────────────────────────────────
int EvaluateSignal() {
   double price = m15_close;
   if(price == 0) return 0;
   
   gateBull = 0; gateBear = 0;
   if(ema20_h1 != 0 && h1_close > ema20_h1)  gateBull++;
   if(ema50_h1 != 0 && h1_close > ema50_h1)  gateBull++;
   if(ema100_h1 != 0 && h1_close > ema100_h1) gateBull++;
   if(ema200_h1 != 0 && h1_close > ema200_h1) gateBull++;
   if(ema20_h1 != 0 && h1_close < ema20_h1)  gateBear++;
   if(ema50_h1 != 0 && h1_close < ema50_h1)  gateBear++;
   if(ema100_h1 != 0 && h1_close < ema100_h1) gateBear++;
   if(ema200_h1 != 0 && h1_close < ema200_h1) gateBear++;
   
   int gd = 0;
   if(gateBull >= 3) gd = 1; else if(gateBear >= 3) gd = -1;
   else if(gateBull >= 2) gd = 1; else if(gateBear >= 2) gd = -1;
   
   FindNearestSnR(price);
   double atr = (atr_value > 0) ? atr_value : 1;
   bool nearSupport = (nearestSupport > 0 && nearestSupportDist < atr * 1.5);
   bool nearResist  = (nearestResist > 0 && nearestResistDist < atr * 1.5);
   
   bbLowerTouch = (bb_lower > 0 && m15_low <= bb_lower);
   bbUpperTouch = (bb_upper > 0 && m15_high >= bb_upper);
   
   bool rsiOversold   = (rsi_value > 0 && rsi_value < RSI_Oversold);
   bool rsiOverbought = (rsi_value > RSI_Overbought);
   bool rsiTurningUp   = (rsi_value > rsi_prev && rsi_prev < RSI_Oversold);
   bool rsiTurningDown = (rsi_value < rsi_prev && rsi_prev > RSI_Overbought);
   
   bool pv = (atr_10bars_ago > 0);
   atrNaik  = (pv && atr_value > atr_10bars_ago);
   atrTurun = (pv && atr_value < atr_10bars_ago);
   
   bool regimeBuySafe    = (atrTurun && rsi_value > 60);
   bool regimeSellSafe   = (atrTurun && rsi_value < 40);
   bool regimeReversalUp = (atrNaik && rsi_value < 40);
   bool regimeReversalDn = (atrNaik && rsi_value > 60);
   
   int bs = 0, ss = 0;
   if(gd == 1)    bs += 3; if(gd == -1)   ss += 3;
   if(gateBull == 4) bs += 1; if(gateBear == 4) ss += 1;
   if(nearSupport)    bs += 2; if(nearResist)    ss += 2;
   if(bbLowerTouch)   bs += 2; if(bbUpperTouch)  ss += 2;
   if(rsiOversold)    bs += 1; if(rsiOverbought)  ss += 1;
   if(rsiTurningUp)   bs += 1; if(rsiTurningDown) ss += 1;
   if(regimeBuySafe)  bs += 1; if(regimeSellSafe) ss += 1;
   if(regimeReversalUp)  bs += 1; if(regimeReversalDn) ss += 1;
   
   if(bs >= 5 && bs > ss + 2) return 2;
   if(bs >= 4 && bs > ss)     return 1;
   if(ss >= 5 && ss > bs + 2) return -2;
   if(ss >= 4 && ss > bs)     return -1;
   return 0;
}

// ══════════════════════════════════════════════════════════════════
// TRADING FUNCTIONS
// ══════════════════════════════════════════════════════════════════

// ─── COUNT POSITIONS ─────────────────────────────────────────────
int CountPositions() {
   int c = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() == Symbol() && OrderMagicNumber() == Magic_Number)
         c++;
   }
   return c;
}

bool HasBuy() {
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() == Symbol() && OrderMagicNumber() == Magic_Number && OrderType() == OP_BUY)
         return true;
   }
   return false;
}

bool HasSell() {
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() == Symbol() && OrderMagicNumber() == Magic_Number && OrderType() == OP_SELL)
         return true;
   }
   return false;
}

// ─── BROKER LIMIT CHECK ──────────────────────────────────────────
// Adjust SL/TP so it respects broker minimum stop distance
void ApplyBrokerLimits(double &sl, double &tp, int type) {
   int stopLevel = (int)MarketInfo(Symbol(), MODE_STOPLEVEL);
   int freezeLevel = (int)MarketInfo(Symbol(), MODE_FREEZELEVEL);
   int minDist = MathMax(stopLevel, freezeLevel);
   if(minDist <= 0) return;
   
   double minDistPrice = minDist * Point;
   
   if(type == OP_BUY) {
      double minSL = Ask - minDistPrice;
      double minTP = Ask + minDistPrice;
      if(sl > 0 && sl > minSL) sl = minSL; // SL gak boleh lebih deket dari minDist
      if(tp > 0 && tp < minTP) tp = minTP; // TP gak boleh lebih deket dari minDist
      
      // Final check: SL must be below Ask
      if(sl >= Ask - Point) sl = Ask - minDistPrice;
   }
   else if(type == OP_SELL) {
      double minSL = Bid + minDistPrice;
      double minTP = Bid - minDistPrice;
      if(sl > 0 && sl < minSL) sl = minSL;
      if(tp > 0 && tp > minTP) tp = minTP;
      
      if(sl <= Bid + Point) sl = Bid + minDistPrice;
   }
}

// ─── SPREAD CHECK ────────────────────────────────────────────────
bool IsSpreadOK() {
   double spreadPips = (Ask - Bid) / Point;
   if(spreadPips > Max_Spread_Pips) {
      Print("Spread too high: ", spreadPips, " pips (max ", Max_Spread_Pips, ")");
      return false;
   }
   return true;
}

// ─── LOT SIZE CHECK ──────────────────────────────────────────────
double NormalizeLot(double lot) {
   double minLot = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
   double step   = MarketInfo(Symbol(), MODE_LOTSTEP);
   
   if(step > 0) lot = MathRound(lot / step) * step;
   if(lot < minLot) lot = minLot;
   if(lot > maxLot) lot = maxLot;
   return NormalizeDouble(lot, 2);
}

// ─── EXECUTE BUY ─────────────────────────────────────────────────
void ExecuteBuy() {
   if(!IsSpreadOK()) return;
   if(!Allow_Multiple && HasBuy()) { Print("Already have BUY. Skipping."); return; }
   
   double atr = atr_value;
   if(atr <= 0) { Print("No ATR data. Skipping BUY."); return; }
   
   double lot = NormalizeLot(Lot_Size);
   double sl = NormalizeDouble(Ask - atr * ATR_SL_Mult, Digits);
   double tp = NormalizeDouble(Ask + atr * ATR_TP_Mult, Digits);
   ApplyBrokerLimits(sl, tp, OP_BUY);
   
   int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, Slippage, sl, tp, "CCS BUY", Magic_Number, 0, Green);
   if(ticket < 0) {
      int err = GetLastError();
      string msg = "BUY failed: " + IntegerToString(err);
      if(err == 130) msg += " (Invalid stops - adjust broker limits)";
      else if(err == 138) msg += " (Requote)";
      else if(err == 146) msg += " (Trading busy)";
      Print(msg);
   } else {
      Print("BUY opened: #", ticket, " Lot:", lot, " SL:", sl, " TP:", tp);
   }
}

// ─── EXECUTE SELL ────────────────────────────────────────────────
void ExecuteSell() {
   if(!IsSpreadOK()) return;
   if(!Allow_Multiple && HasSell()) { Print("Already have SELL. Skipping."); return; }
   
   double atr = atr_value;
   if(atr <= 0) { Print("No ATR data. Skipping SELL."); return; }
   
   double lot = NormalizeLot(Lot_Size);
   double sl = NormalizeDouble(Bid + atr * ATR_SL_Mult, Digits);
   double tp = NormalizeDouble(Bid - atr * ATR_TP_Mult, Digits);
   ApplyBrokerLimits(sl, tp, OP_SELL);
   
   int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, Slippage, sl, tp, "CCS SELL", Magic_Number, 0, Red);
   if(ticket < 0) {
      int err = GetLastError();
      string msg = "SELL failed: " + IntegerToString(err);
      if(err == 130) msg += " (Invalid stops)";
      else if(err == 138) msg += " (Requote)";
      else if(err == 146) msg += " (Trading busy)";
      Print(msg);
   } else {
      Print("SELL opened: #", ticket, " Lot:", lot, " SL:", sl, " TP:", tp);
   }
}

// ─── CLOSE ALL POSITIONS ─────────────────────────────────────────
void CloseAllPositions() {
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != Magic_Number) continue;
      
      bool closed = false;
      if(OrderType() == OP_BUY)
         closed = OrderClose(OrderTicket(), OrderLots(), Bid, Slippage, clrWhite);
      else if(OrderType() == OP_SELL)
         closed = OrderClose(OrderTicket(), OrderLots(), Ask, Slippage, clrWhite);
      
      if(!closed) Print("Close failed: #", OrderTicket(), " err:", GetLastError());
   }
}

// ─── SET STOP LOSS ───────────────────────────────────────────────
void SetStopLoss() {
   double atr = atr_value;
   if(atr <= 0) return;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != Magic_Number) continue;
      
      double newSL = 0;
      if(OrderType() == OP_BUY) {
         newSL = NormalizeDouble(Bid - atr * ATR_SL_Mult, Digits);
         // Hanya update kalo SL baru > SL lama (ngunci profit)
         if(newSL > OrderStopLoss() || OrderStopLoss() == 0) {
            double dummyTP = OrderTakeProfit();
            int slLevel = (int)MarketInfo(Symbol(), MODE_STOPLEVEL);
            if(newSL < Bid - slLevel * Point) newSL = Bid - slLevel * Point;
            OrderModify(OrderTicket(), OrderOpenPrice(), newSL, dummyTP, 0, clrWhite);
         }
      }
      else if(OrderType() == OP_SELL) {
         newSL = NormalizeDouble(Ask + atr * ATR_SL_Mult, Digits);
         if(newSL < OrderStopLoss() || OrderStopLoss() == 0) {
            double dummyTP = OrderTakeProfit();
            int slLevel = (int)MarketInfo(Symbol(), MODE_STOPLEVEL);
            if(newSL > Ask + slLevel * Point) newSL = Ask + slLevel * Point;
            OrderModify(OrderTicket(), OrderOpenPrice(), newSL, dummyTP, 0, clrWhite);
         }
      }
   }
}

// ─── SET TAKE PROFIT ─────────────────────────────────────────────
void SetTakeProfit() {
   double atr = atr_value;
   if(atr <= 0) return;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != Magic_Number) continue;
      
      double newTP = 0;
      if(OrderType() == OP_BUY) {
         newTP = NormalizeDouble(Bid + atr * ATR_TP_Mult, Digits);
         if(newTP > OrderTakeProfit() || OrderTakeProfit() == 0) {
            OrderModify(OrderTicket(), OrderOpenPrice(), OrderStopLoss(), newTP, 0, clrWhite);
         }
      }
      else if(OrderType() == OP_SELL) {
         newTP = NormalizeDouble(Ask - atr * ATR_TP_Mult, Digits);
         if(newTP < OrderTakeProfit() || OrderTakeProfit() == 0) {
            OrderModify(OrderTicket(), OrderOpenPrice(), OrderStopLoss(), newTP, 0, clrWhite);
         }
      }
   }
}

// ══════════════════════════════════════════════════════════════════
// DRAWING FUNCTIONS
// ══════════════════════════════════════════════════════════════════

// ─── DELETE ALL OBJECTS ───────────────────────────────────────────
void DeleteAllObjects() {
   string p = INDICATOR_NAME + "_";
   for(int i = ObjectsTotal(-1) - 1; i >= 0; i--) {
      string n = ObjectName(i);
      if(StringFind(n, p) == 0) ObjectDelete(0, n);
   }
}

// ─── PANEL ────────────────────────────────────────────────────────
void DrawPanel() {
   string p = INDICATOR_NAME + "_";
   int x = Panel_X, y = Panel_Y;
   
   for(int i = 0; i < 30; i++) ObjectDelete(0, p + "L" + IntegerToString(i));
   ObjectDelete(0, p + "BG");
   
   string l[30]; color lc[30]; int fs[30];
   int cnt = 0;
   double atrS = (atr_value > 0) ? atr_value : 1;
   int gb=0, gs=0;
   if(h1_close>ema20_h1) gb++; else if(h1_close<ema20_h1) gs++;
   if(h1_close>ema50_h1) gb++; else if(h1_close<ema50_h1) gs++;
   if(h1_close>ema100_h1) gb++; else if(h1_close<ema100_h1) gs++;
   if(h1_close>ema200_h1) gb++; else if(h1_close<ema200_h1) gs++;
   
   l[cnt] = "CALLUNK CONFLUENCE SYSTEM"; lc[cnt] = clrWhite; fs[cnt] = 10; cnt++;
   string st = "NEUTRAL"; color sc = clrGray;
   if(signal == 2)  { st = "STRONG BUY";  sc = clrLime; }
   else if(signal == 1)  { st = "BUY";       sc = clrMediumSeaGreen; }
   else if(signal == -1) { st = "SELL";      sc = clrTomato; }
   else if(signal == -2) { st = "STRONG SELL"; sc = clrRed; }
   l[cnt] = "Signal: " + st; lc[cnt] = sc; fs[cnt] = 12; cnt++;
   l[cnt] = "EMA Gates: " + IntegerToString(gb) + "A / " + IntegerToString(gs) + "V";
   lc[cnt] = (gb>gs) ? clrMediumSeaGreen : (gs>gb) ? clrTomato : clrGray; fs[cnt] = 9; cnt++;
   l[cnt] = "E20:"+DoubleToStr(ema20_h1,5)+"  E50:"+DoubleToStr(ema50_h1,5); lc[cnt] = clrWhite; fs[cnt] = 9; cnt++;
   l[cnt] = "E100:"+DoubleToStr(ema100_h1,5)+" E200:"+DoubleToStr(ema200_h1,5); lc[cnt] = clrWhite; fs[cnt] = 9; cnt++;
   l[cnt] = "--- Entry (M15) ---"; lc[cnt] = clrLightGray; fs[cnt] = 9; cnt++;
   string bbs = "BB: Mid";
   if(bbLowerTouch) bbs = "BB: LOW Touch";
   else if(bbUpperTouch) bbs = "BB: HIGH Touch";
   l[cnt] = bbs; lc[cnt] = clrWhite; fs[cnt] = 9; cnt++;
   string rd = (rsi_value>rsi_prev) ? ">" : (rsi_value<rsi_prev) ? "<" : "-";
   color rc = (rsi_value>0 && rsi_value<RSI_Oversold) ? clrLime : (rsi_value>RSI_Overbought) ? clrRed : clrWhite;
   l[cnt] = "RSI:"+DoubleToStr(rsi_value,1)+rd; lc[cnt] = rc; fs[cnt] = 9; cnt++;
   string ad = atrNaik ? ">" : atrTurun ? "<" : "-";
   color ac = atrNaik ? clrOrange : clrWhite;
   l[cnt] = "ATR:"+DoubleToStr(atr_value,1)+ad+" P:"+DoubleToStr(atr_10bars_ago,1); lc[cnt] = ac; fs[cnt] = 9; cnt++;
   string rt = "Reg: Normal"; color rcol = clrGray;
   if(atrTurun && rsi_value>60) { rt = "Reg: Stable Bull"; rcol = clrLimeGreen; }
   else if(atrTurun && rsi_value<40) { rt = "Reg: Stable Bear"; rcol = clrLightSalmon; }
   else if(atrNaik && rsi_value>60) { rt = "Reg: Volatile HiRSI"; rcol = clrOrange; }
   else if(atrNaik && rsi_value<40) { rt = "Reg: Volatile LoRSI"; rcol = clrOrange; }
   l[cnt] = rt; lc[cnt] = rcol; fs[cnt] = 9; cnt++;
   l[cnt] = "--- S/R Levels ---"; lc[cnt] = clrLightGray; fs[cnt] = 9; cnt++;
   string spt = "Sup: --";
   if(nearestSupport>0) spt = "Sup:"+DoubleToStr(nearestSupport,5)+" D:"+DoubleToStr(nearestSupportDist/atrS,1)+"A";
   l[cnt] = spt; lc[cnt] = clrMediumSeaGreen; fs[cnt] = 9; cnt++;
   string rst = "Res: --";
   if(nearestResist>0) rst = "Res:"+DoubleToStr(nearestResist,5)+" D:"+DoubleToStr(nearestResistDist/atrS,1)+"A";
   l[cnt] = rst; lc[cnt] = clrTomato; fs[cnt] = 9; cnt++;
   l[cnt] = "--- Warning ---"; lc[cnt] = clrLightGray; fs[cnt] = 9; cnt++;
   
   bool warnVolatileTop   = (atrNaik && rsi_value > 70);
   bool warnVolatileBot   = (atrNaik && rsi_value < 30);
   bool warnOverbuyBB     = (bbUpperTouch && rsi_value > RSI_Overbought);
   bool warnOversellBB    = (bbLowerTouch && rsi_value > 0 && rsi_value < RSI_Oversold);
   bool warnNearResist    = (nearestResist > 0 && nearestResistDist < atrS * 0.5);
   bool warnNearSupport   = (nearestSupport > 0 && nearestSupportDist < atrS * 0.5);
   bool warnOverExtUp     = (ema20_h1 > 0 && m15_close > ema20_h1 + atrS * 2 && rsi_value > 60);
   bool warnOverExtDown   = (ema20_h1 > 0 && m15_close < ema20_h1 - atrS * 2 && rsi_value < 40);
   bool warnATRSpike      = (atr_10bars_ago > 0 && atr_value > atr_10bars_ago * 1.5);
   bool warnGateConflict  = ((gb >= 3 && signal == -1) || (gs >= 3 && signal == 1));
   bool warnRevUp         = (atrNaik && rsi_value < 35 && rsi_value > rsi_prev && rsi_prev < RSI_Oversold);
   bool warnRevDown       = (atrNaik && rsi_value > 65 && rsi_value < rsi_prev && rsi_prev > RSI_Overbought);
   
   int wc = 0;
   if(warnVolatileTop)  { l[cnt] = "VV Volatile Top - Risk Rev"; lc[cnt] = clrRed; fs[cnt] = 9; cnt++; wc++; }
   if(warnVolatileBot)  { l[cnt] = "VV Volatile Bottom - Rev";  lc[cnt] = clrRed; fs[cnt] = 9; cnt++; wc++; }
   if(warnOverbuyBB)    { l[cnt] = "VV Overbought + BB Touch"; lc[cnt] = clrRed; fs[cnt] = 9; cnt++; wc++; }
   if(warnOversellBB)   { l[cnt] = "VV Oversold + BB Touch";   lc[cnt] = clrRed; fs[cnt] = 9; cnt++; wc++; }
   if(warnNearResist && signal >= 1)  { l[cnt] = "V Near Resist"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnNearSupport && signal <= -1){ l[cnt] = "V Near Support";lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnOverExtUp)    { l[cnt] = "V Overextended Up"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnOverExtDown)  { l[cnt] = "V Overextended Down"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnATRSpike)     { l[cnt] = "V ATR Spike"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnGateConflict) { l[cnt] = "V EMA vs Signal Conflict"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnRevUp && signal <= -1) { l[cnt] = "V Pot. Rev Up"; lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(warnRevDown && signal >= 1){ l[cnt] = "V Pot. Rev Down";lc[cnt] = clrOrange; fs[cnt] = 9; cnt++; wc++; }
   if(wc == 0) { l[cnt] = "Status: No Warning"; lc[cnt] = clrGray; fs[cnt] = 9; cnt++; }
   
   int maxW = 0;
   for(int i = 0; i < cnt; i++) { int tw = StringLen(l[i]) * 7 + 10; if(tw > maxW) maxW = tw; }
   if(maxW < 210) maxW = 210;
   int pw = maxW + 10;
   int ph = cnt * 15 + 6;
   panelHeight = ph + 8;
   
   ObjectCreate(0, p+"BG", OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, p+"BG", OBJPROP_XDISTANCE, x - 4);
   ObjectSetInteger(0, p+"BG", OBJPROP_YDISTANCE, y - 4);
   ObjectSetInteger(0, p+"BG", OBJPROP_XSIZE, pw);
   ObjectSetInteger(0, p+"BG", OBJPROP_YSIZE, ph);
   ObjectSetInteger(0, p+"BG", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, p+"BG", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"BG", OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, p+"BG", OBJPROP_HIDDEN, true);
   ObjectSetInteger(0, p+"BG", OBJPROP_COLOR, Panel_BG_Color);
   ObjectSetInteger(0, p+"BG", OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, p+"BG", OBJPROP_WIDTH, 0);
   
   int cy = y;
   for(int i = 0; i < cnt; i++) {
      AddLabel(p+"L"+IntegerToString(i), x, cy, l[i], lc[i], fs[i]);
      cy += 15;
   }
}

// ─── DRAW BUTTONS ────────────────────────────────────────────────
void DrawButtons() {
   string p = INDICATOR_NAME + "_BTN_";
   int x = Panel_X + 2;
   int bx = x, by = Panel_Y + panelHeight + 4;
   int bw = 50, bh = 24, gap = 4;
   
   // BUY
   ObjectCreate(0, p+"BUY", OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, p+"BUY", OBJPROP_XDISTANCE, bx);
   ObjectSetInteger(0, p+"BUY", OBJPROP_YDISTANCE, by);
   ObjectSetInteger(0, p+"BUY", OBJPROP_XSIZE, bw);
   ObjectSetInteger(0, p+"BUY", OBJPROP_YSIZE, bh);
   ObjectSetInteger(0, p+"BUY", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, p+"BUY", OBJPROP_TEXT, "BUY");
   ObjectSetInteger(0, p+"BUY", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, p+"BUY", OBJPROP_BGCOLOR, clrForestGreen);
   ObjectSetInteger(0, p+"BUY", OBJPROP_BORDER_COLOR, clrDarkGreen);
   ObjectSetInteger(0, p+"BUY", OBJPROP_FONTSIZE, 9);
   ObjectSetString(0, p+"BUY", OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, p+"BUY", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"BUY", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, p+"BUY", OBJPROP_HIDDEN, false);
   bx += bw + gap;
   
   // SELL
   ObjectCreate(0, p+"SELL", OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, p+"SELL", OBJPROP_XDISTANCE, bx);
   ObjectSetInteger(0, p+"SELL", OBJPROP_YDISTANCE, by);
   ObjectSetInteger(0, p+"SELL", OBJPROP_XSIZE, bw);
   ObjectSetInteger(0, p+"SELL", OBJPROP_YSIZE, bh);
   ObjectSetInteger(0, p+"SELL", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, p+"SELL", OBJPROP_TEXT, "SELL");
   ObjectSetInteger(0, p+"SELL", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, p+"SELL", OBJPROP_BGCOLOR, clrCrimson);
   ObjectSetInteger(0, p+"SELL", OBJPROP_BORDER_COLOR, clrDarkRed);
   ObjectSetInteger(0, p+"SELL", OBJPROP_FONTSIZE, 9);
   ObjectSetString(0, p+"SELL", OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, p+"SELL", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"SELL", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, p+"SELL", OBJPROP_HIDDEN, false);
   bx += bw + gap;
   
   // CLOSE
   ObjectCreate(0, p+"CLOSE", OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_XDISTANCE, bx);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_YDISTANCE, by);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_XSIZE, 60);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_YSIZE, bh);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, p+"CLOSE", OBJPROP_TEXT, "CLOSE");
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_BGCOLOR, clrDimGray);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_BORDER_COLOR, clrGray);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_FONTSIZE, 9);
   ObjectSetString(0, p+"CLOSE", OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, p+"CLOSE", OBJPROP_HIDDEN, false);
   
   bx = x; by += bh + gap;
   
   // SET SL
   ObjectCreate(0, p+"SL", OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, p+"SL", OBJPROP_XDISTANCE, bx);
   ObjectSetInteger(0, p+"SL", OBJPROP_YDISTANCE, by);
   ObjectSetInteger(0, p+"SL", OBJPROP_XSIZE, 84);
   ObjectSetInteger(0, p+"SL", OBJPROP_YSIZE, bh);
   ObjectSetInteger(0, p+"SL", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, p+"SL", OBJPROP_TEXT, "SET SL");
   ObjectSetInteger(0, p+"SL", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, p+"SL", OBJPROP_BGCOLOR, clrDarkSlateBlue);
   ObjectSetInteger(0, p+"SL", OBJPROP_BORDER_COLOR, clrMediumPurple);
   ObjectSetInteger(0, p+"SL", OBJPROP_FONTSIZE, 9);
   ObjectSetString(0, p+"SL", OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, p+"SL", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"SL", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, p+"SL", OBJPROP_HIDDEN, false);
   bx += 84 + gap;
   
   // SET TP
   ObjectCreate(0, p+"TP", OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, p+"TP", OBJPROP_XDISTANCE, bx);
   ObjectSetInteger(0, p+"TP", OBJPROP_YDISTANCE, by);
   ObjectSetInteger(0, p+"TP", OBJPROP_XSIZE, 84);
   ObjectSetInteger(0, p+"TP", OBJPROP_YSIZE, bh);
   ObjectSetInteger(0, p+"TP", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, p+"TP", OBJPROP_TEXT, "SET TP");
   ObjectSetInteger(0, p+"TP", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, p+"TP", OBJPROP_BGCOLOR, clrDarkSlateBlue);
   ObjectSetInteger(0, p+"TP", OBJPROP_BORDER_COLOR, clrMediumPurple);
   ObjectSetInteger(0, p+"TP", OBJPROP_FONTSIZE, 9);
   ObjectSetString(0, p+"TP", OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, p+"TP", OBJPROP_BACK, false);
   ObjectSetInteger(0, p+"TP", OBJPROP_SELECTABLE, true);
   ObjectSetInteger(0, p+"TP", OBJPROP_HIDDEN, false);
}

// ─── ON CHART EVENT ──────────────────────────────────────────────
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam) {
   if(id == CHARTEVENT_OBJECT_CLICK) {
      string p = INDICATOR_NAME + "_BTN_";
      
      if(sparam == p + "BUY")   { ExecuteBuy(); ChartRedraw(); }
      else if(sparam == p + "SELL")  { ExecuteSell(); ChartRedraw(); }
      else if(sparam == p + "CLOSE") { CloseAllPositions(); ChartRedraw(); }
      else if(sparam == p + "SL")    { SetStopLoss(); ChartRedraw(); }
      else if(sparam == p + "TP")    { SetTakeProfit(); ChartRedraw(); }
      
      ObjectSetInteger(0, sparam, OBJPROP_STATE, false);
   }
}

// ─── ADD LABEL ────────────────────────────────────────────────────
void AddLabel(string name, int x, int y, string txt, color clr, int sz) {
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, name, OBJPROP_TEXT, txt);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, sz);
   ObjectSetString(0, name, OBJPROP_FONT, "Consolas");
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
}
//+------------------------------------------------------------------+
