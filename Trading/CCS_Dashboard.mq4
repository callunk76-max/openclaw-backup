//+------------------------------------------------------------------+
//|                                               CCS_Dashboard.mq4  |
//|          Callunk Confluence System — EA Dashboard Multi Pair      |
//|                                        Callunk & Cuy              |
//+------------------------------------------------------------------+
#property copyright "Callunk & Cuy"
#property version   "1.02"
#property strict
#property description "CCS Dashboard — 29 Pair EA dengan Trading"
#property description "Klik F+/F- utk ubah ukuran font & layout"

// ===== DISPLAY =====
input int    FontSize     = 8;
input color  TextColor    = clrWhite;
input color  HeaderColor  = clrYellow;
input int    StartX       = 10;
input int    StartY       = 25;

// ===== PAIRS =====
input string CustomPairs  = "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY,XAUUSD";

// ===== TRADING =====
input double LotSize             = 0.01;
input int    MagicNumber         = 20260506;
input int    MaxOpenPositions    = 3;
input int    Slippage            = 10;
input double ATR_SL_Mult         = 1.5;
input double ATR_TP_Mult         = 2.0;

// ===== CCS INDICATORS =====
input int    BB_Period      = 20;
input double BB_Deviation   = 2.0;
input int    RSI_Period     = 14;
input double RSI_Oversold   = 30.0;
input double RSI_Overbought = 70.0;
input int    ATR_Period     = 14;
input int    SnR_BarsLeft   = 3;
input int    SnR_BarsRight  = 3;
input int    SnR_MaxLevels  = 20;
input int    EMA20_Period   = 20;
input int    EMA50_Period   = 50;
input int    EMA100_Period  = 100;
input int    EMA200_Period  = 200;

// ===== CURRENCY STRENGTH =====
input double CS_Strong_Threshold = 5.0; // GAP >= 5 = strong bias

// ===== GLOBALS =====
string pairs[];
int totalPairs;
bool autoTradeON  = false;
bool alertON      = true;
int  runtimeMaxPos = 0;
int  runtimeFontSize = 8;
datetime lastUpdateTime = 0;
int updateCounter = 0;

// ─── CCS DATA PER PAIR ───────────────────────────────────────────
struct CCSData {
   string pair;
   int    signal;
   int    prevSignal;   // buat hysteresis
   int    gateBull;
   int    gateBear;
   double rsi;
   double atr;
   bool   bbTouchLow;
   bool   bbTouchHigh;
   bool   atrNaik;
   string regime;
   string warning;
   double nearestSup;
   double nearestRes;
   double ccyGap;       // currency strength gap (0.0 - 9.0)
};

CCSData ccsData[];
string lastAlertSignal[];
datetime lastAlertTime[];

// ─── TRAILING STOP ──────────────────────────────────────────────
struct TrailData {
   int ticket;
   double peak;     // BUY: highest price / SELL: lowest price
   bool active;     // trailing sudah aktif?
};
TrailData trailData[];
int trailCount = 0;

// ─── CURRENCY NAMES ───────────────────────────────────────────────
string ccyList[8] = {"USD","EUR","GBP","CHF","CAD","AUD","JPY","NZD"};
int ccyIdx(string c) {
   for(int i=0;i<8;i++) if(ccyList[i]==c) return i;
   return -1;
}

// ===== INIT =====
int OnInit() {
   runtimeMaxPos = MaxOpenPositions;
   runtimeFontSize = FontSize;
   BuildPairs();
   ArrayResize(ccsData, totalPairs);
   ArrayResize(lastAlertSignal, totalPairs);
   ArrayResize(lastAlertTime, totalPairs);
   for(int i=0;i<totalPairs;i++) { ccsData[i].prevSignal=0; lastAlertSignal[i]=""; lastAlertTime[i]=0; }
   CreateDashboard();
   ArrayResize(trailData, 50); // max 50 tracked positions
   trailCount = 0;
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}

// ===== DEINIT =====
void OnDeinit(const int reason) {
   EventKillTimer();
   DeleteAllObjects();
}

// ===== BUILD PAIRS =====
void BuildPairs() {
   string s = CustomPairs;
   StringReplace(s," ","");
   totalPairs = 1;
   for(int i=0;i<StringLen(s);i++) if(StringGetCharacter(s,i)==',') totalPairs++;
   ArrayResize(pairs,totalPairs);
   int start=0,idx=0;
   for(int i=0;i<=StringLen(s);i++) {
      if(i==StringLen(s)||StringGetCharacter(s,i)==',') {
         if(i>start) { string p=StringSubstr(s,start,i-start); if(StringLen(p)>0) pairs[idx++]=p; }
         start=i+1;
      }
   }
   totalPairs=idx;
   ArrayResize(pairs,totalPairs);
}

// ===== ONTICK =====
void OnTick() {
   datetime now = TimeCurrent();
   if(now == lastUpdateTime) return;
   lastUpdateTime = now;
   updateCounter++;
   UpdateAllSignals();
   if(updateCounter%2==0 && autoTradeON) RunAutoTrade();
   ManageTrailingStops();
   UpdateDashboard();
}

// ===== ONTIMER =====
void OnTimer() {
   datetime now = TimeCurrent();
   if(now == lastUpdateTime) return;
   lastUpdateTime = now;
   updateCounter++;
   UpdateAllSignals();
   if(updateCounter%2==0) { CheckAlerts(); if(autoTradeON) RunAutoTrade(); }
   ManageTrailingStops();
   UpdateDashboard();
}

// ===== ONCHARTEVENT =====
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam) {
   if(id!=CHARTEVENT_OBJECT_CLICK) return;
   
   if(sparam=="BtnAutoTrade") { autoTradeON=!autoTradeON; UpdateAutoTradeBtn(); ChartRedraw(); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   if(sparam=="BtnAlert")     { alertON=!alertON;         UpdateAlertBtn();     ChartRedraw(); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   if(sparam=="HeaderCloseAll") { CloseAllPositions(); ChartRedraw(); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   if(sparam=="BtnFontMinus") { ResizeFont(runtimeFontSize-1); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   if(sparam=="BtnFontPlus")  { ResizeFont(runtimeFontSize+1); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   
   if(StringFind(sparam,"BtnBuy_")==0) {
      int i=(int)StringToInteger(StringSubstr(sparam,7));
      if(i>=0&&i<totalPairs) { OpenTrade(pairs[i],OP_BUY); ChartRedraw(); }
      ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"BtnSell_")==0) {
      int i=(int)StringToInteger(StringSubstr(sparam,8));
      if(i>=0&&i<totalPairs) { OpenTrade(pairs[i],OP_SELL); ChartRedraw(); }
      ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"BtnClose_")==0) {
      int i=(int)StringToInteger(StringSubstr(sparam,9));
      if(i>=0&&i<totalPairs) { CloseSymbol(pairs[i]); ChartRedraw(); }
      ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"MaxMinus")==0) { if(runtimeMaxPos>1) runtimeMaxPos--; UpdateMaxOrder(); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
   if(StringFind(sparam,"MaxPlus")==0)  { if(runtimeMaxPos<10) runtimeMaxPos++; UpdateMaxOrder(); ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false); return; }
}

// ===== MANAGE TRAILING STOPS =====
void ManageTrailingStops() {
   // Sync trailData with open orders (remove closed ones)
   for(int t=trailCount-1; t>=0; t--) {
      bool found = false;
      for(int j=0;j<OrdersTotal();j++) {
         if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
         if(OrderTicket()==trailData[t].ticket) { found=true; break; }
      }
      if(!found) {
         // Remove by shifting
         for(int k=t; k<trailCount-1; k++) trailData[k]=trailData[k+1];
         trailCount--;
      }
   }
   
   // Update trail for each open position
   for(int j=0;j<OrdersTotal();j++) {
      if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber) continue;
      if(OrderType()!=OP_BUY && OrderType()!=OP_SELL) continue;
      
      int ticket = OrderTicket();
      string sym = OrderSymbol();
      double atrH1 = iATR(sym, PERIOD_H1, ATR_Period, 0);
      if(atrH1 <= 0) continue;
      
      // Find trail data for this ticket
      int ti = -1;
      for(int t=0; t<trailCount; t++) {
         if(trailData[t].ticket == ticket) { ti=t; break; }
      }
      
      bool isBuy = (OrderType() == OP_BUY);
      double currentPrice = isBuy ? SymbolInfoDouble(sym,SYMBOL_BID) : SymbolInfoDouble(sym,SYMBOL_ASK);
      double openPrice = OrderOpenPrice();
      double currentSL = OrderStopLoss();
      double profitPips = isBuy ? (currentPrice - openPrice) : (openPrice - currentPrice);
      
      // Activation threshold: ATR_H1 * 1.0
      // Trail distance: ATR_H1 * 0.8
      double activate = atrH1 * 1.0;
      double trailDist = atrH1 * 0.8;
      int digits = (int)MarketInfo(sym,MODE_DIGITS);
      
      if(ti < 0) {
         // New position — add to tracking
         ti = trailCount;
         trailData[ti].ticket = ticket;
         trailData[ti].peak = isBuy ? currentPrice : currentPrice;
         trailData[ti].active = false;
         trailCount++;
      }
      
      // Update peak
      if(isBuy) {
         if(currentPrice > trailData[ti].peak) trailData[ti].peak = currentPrice;
      } else {
         if(currentPrice < trailData[ti].peak) trailData[ti].peak = currentPrice;
      }
      
      // Activate trailing when profit >= ATR*1.0
      if(!trailData[ti].active) {
         if(profitPips >= activate) {
            trailData[ti].active = true;
            Print("Trailing activated for #", ticket);
         }
      }
      
      // Calculate new SL
      if(trailData[ti].active) {
         double newSL;
         if(isBuy) {
            newSL = trailData[ti].peak - trailDist;
            // Only update SL UP (never down) and minimum step
            if(newSL > currentSL + atrH1*0.2 || currentSL == 0) {
               newSL = NormalizeDouble(newSL, digits);
               int stopLevel = (int)MarketInfo(sym, MODE_STOPLEVEL);
               double minSL = currentPrice - stopLevel * SymbolInfoDouble(sym,SYMBOL_POINT);
               if(newSL < minSL) newSL = minSL;
               OrderModify(ticket, openPrice, newSL, OrderTakeProfit(), 0, clrWhite);
            }
         } else {
            newSL = trailData[ti].peak + trailDist;
            if(newSL < currentSL - atrH1*0.2 || currentSL == 0) {
               newSL = NormalizeDouble(newSL, digits);
               int stopLevel = (int)MarketInfo(sym, MODE_STOPLEVEL);
               double maxSL = currentPrice + stopLevel * SymbolInfoDouble(sym,SYMBOL_POINT);
               if(newSL > maxSL) newSL = maxSL;
               OrderModify(ticket, openPrice, newSL, OrderTakeProfit(), 0, clrWhite);
            }
         }
      }
   }
}

void RemoveTrailData(int ticket) {
   for(int t=trailCount-1; t>=0; t--) {
      if(trailData[t].ticket == ticket) {
         for(int k=t; k<trailCount-1; k++) trailData[k]=trailData[k+1];
         trailCount--;
         break;
      }
   }
}

// ===== RESIZE FONT =====
void ResizeFont(int newSize) {
   if(newSize<6 || newSize>22) return;
   runtimeFontSize = newSize;
   DeleteAllObjects();
   CreateDashboard();
   ChartRedraw();
}

// ===== UPDATE ALL SIGNALS =====
void UpdateAllSignals() {
   // Step 1: Hitung currency strength dulu
   CalcCurrencyStrength();
   
   // Step 2: Hitung signal per pair + hysteresis
   for(int i=0;i<totalPairs;i++) {
      int rawSig = CalculateCCS_Signal(pairs[i], i);
      int prevSig = ccsData[i].prevSignal;
      
      // ── Hysteresis: gak boleh flip lgsg ──
      int outSig = rawSig;
      
      // STRONG BUY (2) atau STRONG SELL (-2) gak bisa flip langsung
      if(prevSig >= 2 && rawSig <= -1) outSig = 0; // via neutral dulu
      if(prevSig <= -2 && rawSig >= 1) outSig = 0;
      if(prevSig >= 1 && rawSig <= -2) outSig = 0;
      if(prevSig <= -1 && rawSig >= 2) outSig = 0;
      
      // STRONG -> Regular (step down 1 level)
      if(prevSig == 2 && rawSig == 0) outSig = 1;  // STR BUY -> BUY dulu
      if(prevSig == -2 && rawSig == 0) outSig = -1; // STR SELL -> SELL dulu
      
      // Kalau hasilnya 0, tahan di signal sebelumnya dulu (biar gak cepat hilang)
      if(outSig == 0 && prevSig != 0) {
         // Kasih 2 bar grace period sebelum balik ke neutral
         // Tapi di sini kita gak track bar count, jadi simple: tahan di 1 step turun
      }
      
      ccsData[i].prevSignal = outSig;
      ccsData[i].signal = outSig;
   }
}

// ===== CURRENCY STRENGTH (GIRAIA: DAILY RANGE) =====
// Logic dari currency_strength.pine
double ccyStrength[8] = {0,0,0,0,0,0,0,0};

// Score 0-9 berdasarkan posisi close dalam daily range
int f_pair_score(string sym) {
   double d_close = iClose(sym, PERIOD_D1, 0);
   double d_high  = iHigh(sym, PERIOD_D1, 0);
   double d_low   = iLow(sym, PERIOD_D1, 0);
   if(d_high <= d_low || d_close <= 0) return -1;
   
   double ratio = (d_close - d_low) / (d_high - d_low);
        if(ratio >= 0.97) return 9;
   else if(ratio >= 0.90) return 8;
   else if(ratio >= 0.75) return 7;
   else if(ratio >= 0.60) return 6;
   else if(ratio >= 0.50) return 5;
   else if(ratio >= 0.40) return 4;
   else if(ratio >= 0.25) return 3;
   else if(ratio >= 0.10) return 2;
   else if(ratio >= 0.03) return 1;
   else return 0;
}

void CalcCurrencyStrength() {
   // Skor 28 pair pada D1
   double s[28];
   string p[28] = {"GBPUSD","USDCHF","EURUSD","USDJPY","USDCAD","NZDUSD","AUDUSD",
                    "AUDNZD","AUDCAD","AUDCHF","AUDJPY",
                    "CADJPY","CHFJPY",
                    "EURGBP","EURAUD","EURCHF","EURJPY","EURNZD","EURCAD",
                    "GBPCHF","GBPAUD","GBPCAD","GBPJPY","GBPNZD",
                    "NZDJPY","NZDCAD","CHFCAD","NZDCHF"};
   
   for(int i=0;i<28;i++) s[i] = f_pair_score(p[i]);
   
   // Hitung sum per currency (sesuai Pine asli)
   double su[8] = {0,0,0,0,0,0,0,0};
   
   // USD: index 0
   su[0] = ((9-s[0]) + s[1] + (9-s[2]) + s[3] + s[4] + (9-s[5]) + (9-s[6])) / 7.0;
   // EUR: index 1
   su[1] = (s[2] + s[13] + s[14] + s[15] + s[16] + s[17] + s[18]) / 7.0;
   // GBP: index 2
   su[2] = (s[0] + (9-s[13]) + s[19] + s[20] + s[21] + s[22] + s[23]) / 7.0;
   // CHF: index 3
   su[3] = ((9-s[1]) + (9-s[9]) + s[12] + (9-s[15]) + (9-s[19]) + s[26] + (9-s[27])) / 7.0;
   // CAD: index 4
   su[4] = ((9-s[4]) + (9-s[8]) + s[11] + (9-s[18]) + (9-s[21]) + (9-s[25]) + (9-s[26])) / 7.0;
   // AUD: index 5
   su[5] = (s[6] + s[7] + s[8] + s[9] + s[10] + (9-s[14]) + (9-s[20])) / 7.0;
   // JPY: index 6
   su[6] = ((9-s[3]) + (9-s[10]) + (9-s[11]) + (9-s[12]) + (9-s[16]) + (9-s[22]) + (9-s[24])) / 7.0;
   // NZD: index 7
   su[7] = (s[5] + (9-s[7]) + (9-s[17]) + (9-s[23]) + s[24] + s[25] + s[27]) / 7.0;
   
   for(int ci=0;ci<8;ci++) ccyStrength[ci] = su[ci];
}

double GetCCYGap(string sym) {
   string base="", quote="";
   if(sym=="XAUUSD") { base="XAU"; quote="USD"; }
   else if(StringLen(sym)==6) { base=StringSubstr(sym,0,3); quote=StringSubstr(sym,3,3); }
   else return 0;
   int bi=ccyIdx(base), qi=ccyIdx(quote);
   if(bi<0||qi<0) return 0;
   double raw = ccyStrength[bi] - ccyStrength[qi];
   return NormalizeDouble(raw, 1);
}

// ===== CCS SIGNAL =====
int CalculateCCS_Signal(string sym, int idx) {
   if(!IsSymbolAvailable(sym)) return 0;
   
   int tf_h1 = PERIOD_H1;
   
   double h1_close  = iClose(sym, tf_h1, 0);
   double ema20    = iMA(sym, tf_h1, EMA20_Period,  0, MODE_EMA, PRICE_CLOSE, 0);
   double ema50    = iMA(sym, tf_h1, EMA50_Period,  0, MODE_EMA, PRICE_CLOSE, 0);
   double ema100   = iMA(sym, tf_h1, EMA100_Period, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema200   = iMA(sym, tf_h1, EMA200_Period, 0, MODE_EMA, PRICE_CLOSE, 0);
   double bb_lower = iBands(sym, tf_h1, BB_Period, BB_Deviation, 0, PRICE_CLOSE, MODE_LOWER, 0);
   double bb_upper = iBands(sym, tf_h1, BB_Period, BB_Deviation, 0, PRICE_CLOSE, MODE_UPPER, 0);
   double rsi_val  = iRSI(sym, tf_h1, RSI_Period, PRICE_CLOSE, 0);
   double rsi_prev = iRSI(sym, tf_h1, RSI_Period, PRICE_CLOSE, 1);
   double atr_val  = iATR(sym, tf_h1, ATR_Period, 0);
   double atr_prev = iATR(sym, tf_h1, ATR_Period, 10);
   double h1_high  = iHigh(sym, tf_h1, 0);
   double h1_low   = iLow(sym, tf_h1, 0);
   
   // Currency Strength Gap
   ccsData[idx].ccyGap = GetCCYGap(sym);
   
   ccsData[idx].rsi = rsi_val;
   ccsData[idx].atr = atr_val;
   ccsData[idx].bbTouchLow  = (bb_lower>0 && h1_low <= bb_lower);
   ccsData[idx].bbTouchHigh = (bb_upper>0 && h1_high >= bb_upper);
   
   if(h1_close==0 || rsi_val==0) return 0;
   
   int gb=0, gs=0;
   if(ema20>0  && h1_close>ema20)  gb++; else if(ema20>0  && h1_close<ema20)  gs++;
   if(ema50>0  && h1_close>ema50)  gb++; else if(ema50>0  && h1_close<ema50)  gs++;
   if(ema100>0 && h1_close>ema100) gb++; else if(ema100>0 && h1_close<ema100) gs++;
   if(ema200>0 && h1_close>ema200) gb++; else if(ema200>0 && h1_close<ema200) gs++;
   ccsData[idx].gateBull=gb; ccsData[idx].gateBear=gs;
   
   double nearSup=0, nearRes=0, nearSupD=999999, nearResD=999999;
   int bars = MathMin(200,iBars(sym,tf_h1));
   if(bars >= SnR_BarsLeft+SnR_BarsRight+1) {
      for(int b=SnR_BarsLeft; b<bars-SnR_BarsRight; b++) {
         double sh = iHigh(sym,tf_h1,b), sl = iLow(sym,tf_h1,b);
         bool isSH=true, isSL=true;
         for(int j=1;j<=SnR_BarsLeft;j++) { if(sh<=iHigh(sym,tf_h1,b+j)) isSH=false; if(sl>=iLow(sym,tf_h1,b+j)) isSL=false; }
         for(int j=1;j<=SnR_BarsRight;j++){ if(sh<=iHigh(sym,tf_h1,b-j)) isSH=false; if(sl>=iLow(sym,tf_h1,b-j)) isSL=false; }
         if(isSH && isSL) continue;
         if(isSH) { double d2=MathAbs(sh-h1_close); if(h1_close<sh && d2<nearResD) { nearRes=sh; nearResD=d2; } }
         if(isSL) { double d3=MathAbs(sl-h1_close); if(h1_close>sl && d3<nearSupD) { nearSup=sl; nearSupD=d3; } }
      }
   }
   ccsData[idx].nearestSup = nearSup;
   ccsData[idx].nearestRes = nearRes;
   
   double atrS = (atr_val>0) ? atr_val : 1;
   bool nearSupport = (nearSup>0 && nearSupD < atrS*1.5);
   bool nearResist  = (nearRes>0 && nearResD < atrS*1.5);
   
   bool rsiOversold  = (rsi_val>0 && rsi_val<RSI_Oversold);
   bool rsiOverbought= (rsi_val>RSI_Overbought);
   bool rsiTurningUp = (rsi_val>rsi_prev && rsi_prev<RSI_Oversold);
   bool rsiTurningDn = (rsi_val<rsi_prev && rsi_prev>RSI_Overbought);
   
   bool pv = (atr_prev>0);
   bool atrNaik2 = (pv && atr_val>atr_prev);
   bool atrTurun = (pv && atr_val<atr_prev);
   ccsData[idx].atrNaik = atrNaik2;
   
   string volTxt = "=Nor"; color volCol = clrGray;
   if(atrTurun) { volTxt = "Sta"; volCol = clrLimeGreen; }
   else if(atrNaik2) { volTxt = "Vol"; volCol = clrOrange; }
   ccsData[idx].regime = volTxt;
   
   // ── SCORING: GAP AS GATEKEEPER ──
   double gap = ccsData[idx].ccyGap;
   
   // GAP Gate: GAP must be >= 5 to allow directional bias
   bool gapBull = (gap >= CS_Strong_Threshold);
   bool gapBear = (gap <= -CS_Strong_Threshold);
   
   int bs=0, ss=0;
   
   // Only ALLOW scoring in the GAP direction
   if(gapBull) {
      // EMA Gates (30%) — max 3
      if(gb >= 4) bs += 3;
      else if(gb >= 3) bs += 2;
      else if(gb >= 2) bs += 1;
      
      // BB + RSI Entry Trigger (20%) — max +1
      if(ccsData[idx].bbTouchLow && rsiOversold) bs += 1;
      else if(rsiTurningUp) bs += 1;
      
      // VOL Modifier (15%) — ±1
      if(atrTurun) bs += 1;
      else if(atrNaik2) bs -= 1;
      
      // SnR Proximity (10%) — max 1
      if(nearSupport) bs += 1;
      
      // GAP ≥ 7 bonus
      if(gap >= 7.0) bs += 2;
      
      // Conflict penalty: EMA gates opposite GAP
      if(gs > gb) bs -= 2;
   }
   else if(gapBear) {
      // EMA Gates (30%) — max 3
      if(gs >= 4) ss += 3;
      else if(gs >= 3) ss += 2;
      else if(gs >= 2) ss += 1;
      
      // BB + RSI Entry Trigger (20%) — max +1
      if(ccsData[idx].bbTouchHigh && rsiOverbought) ss += 1;
      else if(rsiTurningDn) ss += 1;
      
      // VOL Modifier (15%) — ±1
      if(atrTurun) ss += 1;
      else if(atrNaik2) ss -= 1;
      
      // SnR Proximity (10%) — max 1
      if(nearResist) ss += 1;
      
      // GAP ≤ -7 bonus
      if(gap <= -7.0) ss += 2;
      
      // Conflict penalty: EMA gates opposite GAP
      if(gb > gs) ss -= 2;
   }
   else {
      // GAP < 5: NO TRADING — neutral
      ccsData[idx].warning = "NoGAP";
      return 0;
   }
   
   // Warning text
   string w = "";
   if(atrNaik2 && rsi_val>70)              w = "VolTop";
   else if(atrNaik2 && rsi_val<30)         w = "VolBot";
   else if(ccsData[idx].bbTouchHigh && rsiOverbought) w = "OB+BB";
   else if(ccsData[idx].bbTouchLow  && rsiOversold)   w = "OS+BB";
   else if(nearResist && gb>=3)            w = "~Res";
   else if(nearSupport && gs>=3)           w = "~Sup";
   else if(atr_prev>0 && atr_val>atr_prev*1.5) w = "ATR+";
   ccsData[idx].warning = w;
   
   // Final threshold
   if(bs >= 7) return 2;  // STRONG BUY
   if(bs >= 4) return 1;  // BUY
   if(ss >= 7) return -2; // STRONG SELL
   if(ss >= 4) return -1; // SELL
   return 0;
}

// ===== DASHBOARD UI =====
void CreateDashboard() {
   int x=StartX, y=StartY, fs=runtimeFontSize;
   int useLH = (int)(fs * 1.8 + 1);
   double cs = (double)fs / 8.0; // col scale: fs=8 → 1.0, fs=12 → 1.5, fs=16 → 2.0
   if(cs < 1.0) cs = 1.0;
   
   int c0 = x;
   int c1 = x + (int)(50 * cs);     // PAIR
   int c2 = c1 + (int)(60 * cs);    // PROFIT
   int c3 = c2 + (int)(65 * cs);    // SIGNAL
   int c4 = c3 + (int)(60 * cs);    // GAP
   int c5 = c4 + (int)(60 * cs);    // GATES
   int c6 = c5 + (int)(45 * cs);    // RSI
   int c7 = c6 + (int)(40 * cs);    // VOL
   int c8 = c7 + (int)(55 * cs);    // WARN
   int c9 = c8 + (int)(35 * cs);    // BUY
   int c10= c9 + (int)(35 * cs);    // SELL
   int totalW = c10 + (int)(50 * cs) + 20; // total width
   
   int btnH = useLH - 2;
   if(btnH < 12) btnH = 12;
   
   // ── HEADERS ──
   CreateLabel("H_Pair","PAIR",     c0, y, HeaderColor, fs);
   CreateLabel("H_Profit","PL",     c1, y, HeaderColor, fs);
   CreateLabel("H_Signal","SIG",    c2, y, HeaderColor, fs);
   CreateLabel("H_Gap","GAP",       c3, y, HeaderColor, fs);
   CreateLabel("H_Gates","GT",      c4, y, HeaderColor, fs);
   CreateLabel("H_RSI","RSI",       c5, y, HeaderColor, fs);
   CreateLabel("H_Vol","VOL",       c6, y, HeaderColor, fs);
   CreateLabel("H_Warn","WARN",     c7, y, HeaderColor, fs);
   CreateButton("HeaderCloseAll","CLOSE", c8, y-2, (int)(90*cs), 18, clrGray, clrBlack);
   
   y += useLH + 5;
   
   // ── ROWS ──
   for(int i=0;i<totalPairs;i++) {
      int ry = y + i*useLH;
      
      string bg = "RowBG_"+IntegerToString(i);
      ObjectCreate(0,bg,OBJ_RECTANGLE_LABEL,0,0,0);
      ObjectSetInteger(0,bg,OBJPROP_XDISTANCE,x);
      ObjectSetInteger(0,bg,OBJPROP_YDISTANCE,ry);
      ObjectSetInteger(0,bg,OBJPROP_XSIZE,totalW);
      ObjectSetInteger(0,bg,OBJPROP_YSIZE,useLH-1);
      ObjectSetInteger(0,bg,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,bg,OBJPROP_BGCOLOR,RGB(35,35,35));
      ObjectSetInteger(0,bg,OBJPROP_BORDER_COLOR,RGB(50,50,50));
      ObjectSetInteger(0,bg,OBJPROP_BACK,true);
      ObjectSetInteger(0,bg,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,bg,OBJPROP_HIDDEN,true);
      ObjectSetInteger(0,bg,OBJPROP_FONTSIZE,fs);
      
      int ly = ry + 1;
      CreateLabel("Pair_"+IntegerToString(i),   pairs[i], c0, ly, TextColor, fs);
      CreateLabel("Profit_"+IntegerToString(i), "--",      c1, ly, clrGray,  fs);
      CreateLabel("Signal_"+IntegerToString(i), "WAIT",    c2, ly, clrGray,  fs);
      CreateLabel("Gap_"+IntegerToString(i),    "--",      c3, ly, clrGray,  fs);
      CreateLabel("Gates_"+IntegerToString(i),  "--",      c4, ly, clrGray,  fs);
      CreateLabel("RSI_"+IntegerToString(i),    "--",      c5, ly, clrGray,  fs);
      CreateLabel("Vol_"+IntegerToString(i),    "--",      c6, ly, clrGray,  fs);
      CreateLabel("Warn_"+IntegerToString(i),   "",        c7, ly, clrGray,  fs);
      CreateButton("BtnBuy_"+IntegerToString(i),  "B", c8, ry+1, (int)(30*cs), btnH, clrForestGreen, clrWhite);
      CreateButton("BtnSell_"+IntegerToString(i), "S", c9, ry+1, (int)(30*cs), btnH, clrCrimson, clrWhite);
      CreateButton("BtnClose_"+IntegerToString(i),"NO",c10,ry+1, (int)(40*cs), btnH, clrGray, clrBlack);
   }
   
   // ── BOTTOM ──
   int botY = y + (totalPairs+1)*useLH;
   CreateLabel("L_Max","MAX:",x, botY, HeaderColor, fs);
   CreateButton("MaxMinus","-", x+(int)(35*cs), botY-2, (int)(18*cs), (int)(14*cs), clrRed, clrWhite);
   CreateLabel("L_MaxVal",IntegerToString(runtimeMaxPos), x+(int)(55*cs), botY, clrLime, fs);
   CreateButton("MaxPlus","+", x+(int)(75*cs), botY-2, (int)(18*cs), (int)(14*cs), clrLime, clrBlack);
   
   int botY2 = botY + useLH;
   int b = x;
   CreateLabel("L_Bal","BAL:", b, botY2, HeaderColor, fs); b += (int)(35*cs);
   CreateLabel("L_BalVal","$0", b, botY2, clrLime, fs); b += (int)(55*cs);
   CreateLabel("L_Margin","MAR:", b, botY2, HeaderColor, fs); b += (int)(35*cs);
   CreateLabel("L_MarginVal","$0", b, botY2, clrLime, fs); b += (int)(55*cs);
   CreateButton("BtnFontMinus","F-", b, botY2-2, (int)(22*cs), (int)(16*cs), clrGray, clrWhite); b += (int)(28*cs);
   CreateLabel("L_FontVal","F:"+IntegerToString(runtimeFontSize), b, botY2, clrLightGray, fs); b += (int)(35*cs);
   CreateButton("BtnFontPlus","F+", b, botY2-2, (int)(22*cs), (int)(16*cs), clrLime, clrBlack); b += (int)(40*cs);
   CreateButton("BtnAutoTrade","AUTO:OFF", b, botY2-2, (int)(80*cs), (int)(16*cs), C'50,50,50', clrGray); b += (int)(85*cs);
   CreateButton("BtnAlert","ALERT:ON", b, botY2-2, (int)(70*cs), (int)(16*cs), C'0,100,0', clrLime);
}

// ===== UPDATE DASHBOARD =====
void UpdateDashboard() {
   for(int i=0;i<totalPairs;i++) {
      string sigTxt = "WAIT"; color sigCol = clrGray;
      switch(ccsData[i].signal) {
         case 2:  sigTxt="STRBUY"; sigCol=clrLime; break;
         case 1:  sigTxt="BUY";     sigCol=clrMediumSeaGreen; break;
         case -1: sigTxt="SELL";    sigCol=clrTomato; break;
         case -2: sigTxt="STRSEL"; sigCol=clrRed; break;
      }
      ObjectSetString(0,"Signal_"+IntegerToString(i),OBJPROP_TEXT,sigTxt);
      ObjectSetInteger(0,"Signal_"+IntegerToString(i),OBJPROP_COLOR,sigCol);
      
      // GAP
      double gv = ccsData[i].ccyGap;
      string gt2 = DoubleToString(MathAbs(gv), 1);
      color gc2 = (gv>=CS_Strong_Threshold) ? clrLime : (gv<=-CS_Strong_Threshold) ? clrRed : clrGray;
      ObjectSetString(0,"Gap_"+IntegerToString(i),OBJPROP_TEXT,gt2);
      ObjectSetInteger(0,"Gap_"+IntegerToString(i),OBJPROP_COLOR,gc2);
      
      string gt = IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear);
      color gc = (ccsData[i].gateBull>ccsData[i].gateBear) ? clrMediumSeaGreen : (ccsData[i].gateBear>ccsData[i].gateBull) ? clrTomato : clrGray;
      ObjectSetString(0,"Gates_"+IntegerToString(i),OBJPROP_TEXT,gt);
      ObjectSetInteger(0,"Gates_"+IntegerToString(i),OBJPROP_COLOR,gc);
      
      string rt = DoubleToString(ccsData[i].rsi,1);
      color rc = (ccsData[i].rsi>0 && ccsData[i].rsi<RSI_Oversold) ? clrLime : (ccsData[i].rsi>RSI_Overbought) ? clrRed : clrWhite;
      ObjectSetString(0,"RSI_"+IntegerToString(i),OBJPROP_TEXT,rt);
      ObjectSetInteger(0,"RSI_"+IntegerToString(i),OBJPROP_COLOR,rc);
      
      ObjectSetString(0,"Vol_"+IntegerToString(i),OBJPROP_TEXT,ccsData[i].regime);
      color volCol = clrGray;
      if(ccsData[i].regime=="Sta") volCol=clrLimeGreen;
      else if(ccsData[i].regime=="Vol") volCol=clrOrange;
      ObjectSetInteger(0,"Vol_"+IntegerToString(i),OBJPROP_COLOR,volCol);
      
      ObjectSetString(0,"Warn_"+IntegerToString(i),OBJPROP_TEXT,ccsData[i].warning);
      color wc = clrGray;
      if(StringFind(ccsData[i].warning,"Vol")==0||StringFind(ccsData[i].warning,"OB+")==0||StringFind(ccsData[i].warning,"OS+")==0) wc=clrRed;
      else if(StringLen(ccsData[i].warning)>0) wc=clrOrange;
      ObjectSetInteger(0,"Warn_"+IntegerToString(i),OBJPROP_COLOR,wc);
      
      double prof=0; int oc=0; bool hasB=false, hasS=false;
      for(int j=0;j<OrdersTotal();j++) {
         if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
         if(OrderSymbol()!=pairs[i]||OrderMagicNumber()!=MagicNumber) continue;
         prof+=OrderProfit()+OrderSwap()+OrderCommission();
         oc++; if(OrderType()==OP_BUY) hasB=true; if(OrderType()==OP_SELL) hasS=true;
      }
      
      string pt = (oc>0) ? ((prof>=0?"+":"")+DoubleToString(prof,2)) : "--";
      color pc = (oc>0) ? (prof>=0?clrLime:clrRed) : clrGray;
      ObjectSetString(0,"Profit_"+IntegerToString(i),OBJPROP_TEXT,pt);
      ObjectSetInteger(0,"Profit_"+IntegerToString(i),OBJPROP_COLOR,pc);
      
      string ct = "NO"; color cb = clrGray; color ct2 = clrBlack;
      if(oc>0) {
         if(hasB&&hasS) ct="ALL";
         else if(hasB) ct="BUY";
         else ct="SEL";
         cb = (prof>=0) ? clrLime : clrRed;
         ct2 = (prof>=0) ? clrBlack : clrWhite;
      }
      ObjectSetString(0,"BtnClose_"+IntegerToString(i),OBJPROP_TEXT,ct);
      ObjectSetInteger(0,"BtnClose_"+IntegerToString(i),OBJPROP_BGCOLOR,cb);
      ObjectSetInteger(0,"BtnClose_"+IntegerToString(i),OBJPROP_COLOR,ct2);
   }
   
   double totProf=0; int totOcc=0;
   for(int j=0;j<OrdersTotal();j++) {
      if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber) continue;
      totProf+=OrderProfit()+OrderSwap()+OrderCommission();
      totOcc++;
   }
   ObjectSetString(0,"L_BalVal",OBJPROP_TEXT,"$"+DoubleToString(AccountBalance(),2));
   ObjectSetString(0,"L_MarginVal",OBJPROP_TEXT,"$"+DoubleToString(AccountFreeMargin(),2));
   
   string closeAllTxt = "CLOSE";
   color cab=clrGray, cat=clrBlack;
   if(totOcc>0) {
      closeAllTxt = (totProf>=0?"+":"")+DoubleToString(totProf,0);
      cab = (totProf>=0) ? clrLime : clrRed;
      cat = (totProf>=0) ? clrBlack : clrWhite;
   }
   closeAllTxt += " ("+IntegerToString(totOcc)+"/"+IntegerToString(runtimeMaxPos)+")";
   ObjectSetString(0,"HeaderCloseAll",OBJPROP_TEXT,closeAllTxt);
   ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_BGCOLOR,cab);
   ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_COLOR,cat);
   
   UpdateAutoTradeBtn();
   UpdateAlertBtn();
   ChartRedraw();
}

// ===== HELPERS =====
bool IsSymbolAvailable(string sym) { return (MarketInfo(sym,MODE_BID)>0); }
color RGB(int r,int g,int b) { return (color)((r&0xFF)|((g&0xFF)<<8)|((b&0xFF)<<16)); }

void CreateLabel(string name, string text, int x, int y, color clr, int sz) {
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_LABEL,0,0,0);
   ObjectSetInteger(0,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
   ObjectSetString(0,name,OBJPROP_TEXT,text);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,sz);
   ObjectSetString(0,name,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,name,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
}

void CreateButton(string name, string text, int x, int y, int w, int h, color bg, color txtCol) {
   if(ObjectFind(0,name)<0) ObjectCreate(0,name,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,name,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,name,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,name,OBJPROP_YSIZE,h);
   ObjectSetString(0,name,OBJPROP_TEXT,text);
   ObjectSetInteger(0,name,OBJPROP_COLOR,txtCol);
   ObjectSetInteger(0,name,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,name,OBJPROP_BORDER_COLOR,clrGray);
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,runtimeFontSize);
   ObjectSetString(0,name,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,name,OBJPROP_BACK,false);
   ObjectSetInteger(0,name,OBJPROP_SELECTABLE,true);
   ObjectSetInteger(0,name,OBJPROP_SELECTED,false);
}

void DeleteAllObjects() {
   for(int i=ObjectsTotal(-1)-1;i>=0;i--) {
      string n=ObjectName(i);
      if(StringFind(n,"RowBG_")==0||StringFind(n,"Pair_")==0||StringFind(n,"Profit_")==0||
         StringFind(n,"Signal_")==0||StringFind(n,"Gap_")==0||
         StringFind(n,"Gates_")==0||StringFind(n,"RSI_")==0||
         StringFind(n,"Vol_")==0||StringFind(n,"Warn_")==0||
         StringFind(n,"BtnBuy_")==0||StringFind(n,"BtnSell_")==0||StringFind(n,"BtnClose_")==0||
         StringFind(n,"BtnAutoTrade")==0||StringFind(n,"BtnAlert")==0||
         StringFind(n,"BtnFont")==0||
         StringFind(n,"H_")==0||StringFind(n,"L_")==0||StringFind(n,"Header")==0||
         StringFind(n,"Max")==0) ObjectDelete(0,n);
   }
}

void UpdateMaxOrder() { ObjectSetString(0,"L_MaxVal",OBJPROP_TEXT,IntegerToString(runtimeMaxPos)); }

void UpdateAutoTradeBtn() {
   string t=autoTradeON?"AUTO:ON":"AUTO:OFF";
   color b=autoTradeON?clrDarkGreen:C'50,50,50';
   color c=autoTradeON?clrLime:clrGray;
   ObjectSetString(0,"BtnAutoTrade",OBJPROP_TEXT,t);
   ObjectSetInteger(0,"BtnAutoTrade",OBJPROP_BGCOLOR,b);
   ObjectSetInteger(0,"BtnAutoTrade",OBJPROP_COLOR,c);
}

void UpdateAlertBtn() {
   string t=alertON?"ALERT:ON":"ALERT:OFF";
   color b=alertON?C'0,100,0':C'50,50,50';
   color c=alertON?clrLime:clrGray;
   ObjectSetString(0,"BtnAlert",OBJPROP_TEXT,t);
   ObjectSetInteger(0,"BtnAlert",OBJPROP_BGCOLOR,b);
   ObjectSetInteger(0,"BtnAlert",OBJPROP_COLOR,c);
}

// ===== TRADING =====
void OpenTrade(string sym, int type) {
   if(!IsTradeAllowed()) { Print("Trading not allowed"); return; }
   if(!SymbolSelect(sym,true)) { Print("Symbol not found: ",sym); return; }
   int posCount=0;
   for(int j=0;j<OrdersTotal();j++) {
      if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()==MagicNumber && (OrderType()==OP_BUY||OrderType()==OP_SELL)) posCount++;
   }
   if(posCount >= runtimeMaxPos) { Print("Max positions reached"); return; }
   for(int j=0;j<OrdersTotal();j++) {
      if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderSymbol()==sym && OrderMagicNumber()==MagicNumber && OrderType()==type)
         { Print("Already have ",(type==OP_BUY?"BUY":"SELL")," for ",sym); return; }
   }
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK);
   double bid=SymbolInfoDouble(sym,SYMBOL_BID);
   if(ask<=0||bid<=0) { Print("Invalid price for ",sym); return; }
   double lot = NormalizeDouble(LotSize,2);
   double minL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MIN);
   double maxL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MAX);
   if(lot<minL) lot=minL; if(lot>maxL) lot=maxL;
   double atr  = iATR(sym,PERIOD_H1,ATR_Period,0);
   double price = (type==OP_BUY)?ask:bid;
   double sl=0, tp=0;
   if(atr>0) {
      sl = (type==OP_BUY) ? price-atr*ATR_SL_Mult : price+atr*ATR_SL_Mult;
      tp = (type==OP_BUY) ? price+atr*ATR_TP_Mult : price-atr*ATR_TP_Mult;
      int dig=(int)MarketInfo(sym,MODE_DIGITS);
      sl=NormalizeDouble(sl,dig); tp=NormalizeDouble(tp,dig);
   }
   int ticket = OrderSend(sym, type, lot, price, Slippage, sl, tp, "CCS Dash", MagicNumber, 0, clrNONE);
   if(ticket>0) Print("Order #",ticket," ",(type==OP_BUY?"BUY":"SELL")," ",sym," Lot:",lot);
   else {
      Print("OrderSend failed ",sym," err:",GetLastError()," retry without SL/TP");
      ticket=OrderSend(sym,type,lot,price,Slippage,0,0,"CCS Dash",MagicNumber,0,clrNONE);
      if(ticket>0 && atr>0 && OrderSelect(ticket,SELECT_BY_TICKET)) {
         int d2=(int)MarketInfo(sym,MODE_DIGITS);
         sl=(type==OP_BUY)?OrderOpenPrice()-atr*ATR_SL_Mult:OrderOpenPrice()+atr*ATR_SL_Mult;
         tp=(type==OP_BUY)?OrderOpenPrice()+atr*ATR_TP_Mult:OrderOpenPrice()-atr*ATR_TP_Mult;
         OrderModify(ticket,OrderOpenPrice(),NormalizeDouble(sl,d2),NormalizeDouble(tp,d2),0,clrNONE);
      }
   }
}

void CloseSymbol(string sym) {
   for(int i=OrdersTotal()-1;i>=0;i--) {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderSymbol()!=sym||OrderMagicNumber()!=MagicNumber) continue;
      double cp; color ac;
      if(OrderType()==OP_BUY) { cp=SymbolInfoDouble(sym,SYMBOL_BID); ac=clrRed; }
      else { cp=SymbolInfoDouble(sym,SYMBOL_ASK); ac=clrBlue; }
      if(OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac))
         RemoveTrailData(OrderTicket());
      else
         Print("Close fail #",OrderTicket()," err:",GetLastError());
   }
}

void CloseAllPositions() {
   for(int i=OrdersTotal()-1;i>=0;i--) {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber) continue;
      double cp; color ac;
      if(OrderType()==OP_BUY) { cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_BID); ac=clrRed; }
      else { cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK); ac=clrBlue; }
      OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac);
   }
}

// ===== AUTO TRADE =====
void RunAutoTrade() {
   for(int i=0;i<totalPairs;i++) {
      if(ccsData[i].signal!=2 && ccsData[i].signal!=-2) continue;
      string sym = pairs[i];
      int dirType = (ccsData[i].signal==2) ? OP_BUY : OP_SELL;
      int oppType = (ccsData[i].signal==2) ? OP_SELL : OP_BUY;
      bool hasDir=false, hasOpp=false;
      for(int j=0;j<OrdersTotal();j++) {
         if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
         if(OrderSymbol()!=sym||OrderMagicNumber()!=MagicNumber) continue;
         if(OrderType()==dirType) hasDir=true;
         if(OrderType()==oppType) hasOpp=true;
      }
      if(hasOpp) { CloseSymbol(sym); Sleep(200); }
      if(hasDir) continue;
      int tot=0;
      for(int j=0;j<OrdersTotal();j++) {
         if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES)) continue;
         if(OrderMagicNumber()==MagicNumber && (OrderType()==OP_BUY||OrderType()==OP_SELL)) tot++;
      }
      if(tot>=runtimeMaxPos) break;
      OpenTrade(sym,dirType);
   }
}

// ===== ALERTS (sama logic dgn Auto Trade: cuma STRONG) =====
void CheckAlerts() {
   for(int i=0;i<totalPairs;i++) {
      int sig = ccsData[i].signal;
      if(sig != 2 && sig != -2) continue; // cuma STRONG
      
      string dir = (sig==2) ? "STRONG BUY" : "STRONG SELL";
      
      // Cooldown 10 menit biar gak spam
      if(lastAlertSignal[i]==dir && TimeCurrent()-lastAlertTime[i]<600) continue;
      lastAlertSignal[i]=dir;
      lastAlertTime[i]=TimeCurrent();
      
      string w = (StringLen(ccsData[i].warning)>0) ? " ["+ccsData[i].warning+"]" : "";
      string gt = IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear);
      string msg = "CCS: "+dir+" "+pairs[i]+" GAP:"+DoubleToString(MathAbs(ccsData[i].ccyGap),1)+" GT:"+gt+" RSI:"+DoubleToString(ccsData[i].rsi,1)+w;
      if(alertON) { Alert(msg); SendNotification(msg); }
      Print(msg);
   }
}
//+------------------------------------------------------------------+
