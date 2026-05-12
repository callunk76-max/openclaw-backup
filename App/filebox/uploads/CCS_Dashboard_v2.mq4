//+------------------------------------------------------------------+
//|                                         CCS_Dashboard_v2.mq4    |
//|          Callunk Confluence System v2.00 — Improved Edition      |
//|  Perbaikan: Risk management, code quality, robustness, multi-TF  |
//+------------------------------------------------------------------+
#property copyright "Callunk & Cuy — v2.00"
#property version   "2.00"
#property strict
#property description "CCS Dashboard v2 — 29 Pair | Risk-based lot | Multi-TF CS | Drawdown Guard"

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+

// --- Display ---
input int    FontSize        = 8;
input color  TextColor       = clrWhite;
input color  HeaderColor     = clrYellow;
input int    StartX          = 10;
input int    StartY          = 25;

// --- Pairs ---
input string CustomPairs = "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,"
                           "EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,"
                           "GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,"
                           "NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY";

// --- Risk Management ---
input double RiskPercent        = 10.0;   // Risk per trade (% of balance)
input double lot                 = 0.01;
input double MaxDailyDrawdownPct = 50.0;  // Maks drawdown harian (% balance)
input double MaxTotalDrawdownPct = 80.0;  // Maks total drawdown (% balance)
input int    MaxOpenPositions    = 3;    // Maks posisi terbuka
input int    MagicNumber         = 20260506;
input int    Slippage            = 10;
input double MaxSpreadPoints     = 30.0; // Maks spread yang diizinkan (points)

// --- ATR ---
input int    ATR_Period   = 14;
input double ATR_SL_Mult  = 1.5;
input double ATR_TP_Mult  = 2.0;

// --- Bollinger Bands ---
input int    BB_Period    = 20;
input double BB_Deviation = 2.0;

// --- RSI ---
input int    RSI_Period     = 14;
input double RSI_Oversold   = 30.0;
input double RSI_Overbought = 70.0;

// --- EMA ---
input int EMA20_Period  = 20;
input int EMA50_Period  = 50;
input int EMA100_Period = 100;
input int EMA200_Period = 200;

// --- Support & Resistance ---
input int SnR_BarsLeft  = 3;
input int SnR_BarsRight = 3;

// --- Currency Strength ---
input double CS_Strong_Threshold = 5.0;

// --- Auto Trade Cooldown ---
input int AutoTrade_CooldownBars = 3; // Cooldown bar setelah entry sebelum entry lagi

//+------------------------------------------------------------------+
//| CONSTANTS                                                         |
//+------------------------------------------------------------------+
#define MAX_PAIRS      30
#define MAX_TRAIL      60
#define TRAIL_ATR_MULT 0.8
#define TRAIL_ACTIVATE 1.0

//+------------------------------------------------------------------+
//| DATA STRUCTURES                                                   |
//+------------------------------------------------------------------+

// Data sinyal per pair
struct CCSData
{
   string   pair;
   int      signal;
   int      prevSignal;
   int      gateBull;
   int      gateBear;
   int      score;
   double   rsi;
   double   atr;
   double   ccyGap;
   double   snrDist;
   bool     bbTouchLow;
   bool     bbTouchHigh;
   bool     atrRising;
   string   regime;
   string   warning;
   datetime lastEntryTime; // untuk cooldown
};

// Data trailing stop
struct TrailData
{
   int    ticket;
   double peak;
   bool   active;
};

//+------------------------------------------------------------------+
//| GLOBAL VARIABLES                                                  |
//+------------------------------------------------------------------+

string   g_pairs[];
int      g_totalPairs    = 0;
bool     g_autoTradeON   = false;
bool     g_alertON       = true;
int      g_runtimeMaxPos = 0;
int      g_runtimeFontSize = 8;
datetime g_lastUpdateTime  = 0;
int      g_updateCounter   = 0;

CCSData  g_ccsData[];
string   g_lastAlertSignal[];
datetime g_lastAlertTime[];

// Toggle kolom
bool tog_RSI  = true;
bool tog_VOL  = true;
bool tog_SnR  = true;
bool tog_BB   = true;
bool tog_WARN = true;

// Trailing
TrailData g_trailData[MAX_TRAIL];
int       g_trailCount = 0;

// Currency strength
double g_ccyStrength[8] = {0,0,0,0,0,0,0,0};
string g_ccyList[8]     = {"USD","EUR","GBP","CHF","CAD","AUD","JPY","NZD"};

// Drawdown guard
double g_balanceAtDayStart = 0;
double g_peakBalance       = 0;
datetime g_lastDayCheck    = 0;

//+------------------------------------------------------------------+
//| UTILITY: Cari index mata uang                                     |
//+------------------------------------------------------------------+
int CurrencyIndex(string ccy)
{
   for(int i = 0; i < 8; i++)
      if(g_ccyList[i] == ccy) return i;
   return -1;
}

//+------------------------------------------------------------------+
//| UTILITY: Buat warna RGB                                           |
//+------------------------------------------------------------------+
color MakeRGB(int r, int g, int b)
{
   return (color)((r & 0xFF) | ((g & 0xFF) << 8) | ((b & 0xFF) << 16));
}

//+------------------------------------------------------------------+
//| UTILITY: Hitung lot berdasarkan risk %                            |
//+------------------------------------------------------------------+
double CalcLotByRisk(string sym, double slPoints)
{
   double minLotFallback = MarketInfo(sym, MODE_MINLOT);
   if(slPoints <= 0) return minLotFallback;

   double balance    = AccountBalance();
   double riskAmount = balance * RiskPercent / 100.0;
   double tickValue  = MarketInfo(sym, MODE_TICKVALUE);
   double tickSize   = MarketInfo(sym, MODE_TICKSIZE);
   double point      = MarketInfo(sym, MODE_POINT);

   if(tickValue <= 0 || tickSize <= 0) return minLotFallback;

   // Nilai per lot per point
   double valuePerPoint = tickValue / tickSize * point;
   if(valuePerPoint <= 0) return minLotFallback;

   double lot = riskAmount / (slPoints * valuePerPoint);

   double minLot  = MarketInfo(sym, MODE_MINLOT);
   double maxLot  = MarketInfo(sym, MODE_MAXLOT);
   double stepLot = MarketInfo(sym, MODE_LOTSTEP);

   // Bulatkan ke step lot
   lot = MathFloor(lot / stepLot) * stepLot;
   lot = MathMax(minLot, MathMin(maxLot, lot));

   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| UTILITY: Cek apakah spread masih dalam batas                      |
//+------------------------------------------------------------------+
bool IsSpreadOK(string sym)
{
   double spread = MarketInfo(sym, MODE_SPREAD);
   return (spread <= MaxSpreadPoints);
}

//+------------------------------------------------------------------+
//| DRAWDOWN GUARD: Cek apakah trading masih diizinkan               |
//+------------------------------------------------------------------+
bool IsDrawdownOK()
{
   double balance = AccountBalance();
   double equity  = AccountEquity();

   // Reset harian
   datetime now = TimeCurrent();
   MqlDateTime dt_now, dt_last;
   TimeToStruct(now, dt_now);
   TimeToStruct(g_lastDayCheck, dt_last);

   if(dt_now.day != dt_last.day || g_lastDayCheck == 0)
   {
      g_balanceAtDayStart = balance;
      g_lastDayCheck      = now;
   }

   // Update peak balance
   if(balance > g_peakBalance) g_peakBalance = balance;

   // Cek drawdown harian
   if(g_balanceAtDayStart > 0)
   {
      double dailyDD = (g_balanceAtDayStart - equity) / g_balanceAtDayStart * 100.0;
      if(dailyDD >= MaxDailyDrawdownPct) return false;
   }

   // Cek total drawdown dari peak
   if(g_peakBalance > 0)
   {
      double totalDD = (g_peakBalance - equity) / g_peakBalance * 100.0;
      if(totalDD >= MaxTotalDrawdownPct) return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| INIT                                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   g_runtimeMaxPos    = MaxOpenPositions;
   g_runtimeFontSize  = FontSize;
   g_peakBalance      = AccountBalance();
   g_balanceAtDayStart = AccountBalance();
   g_lastDayCheck     = TimeCurrent();

   // Parse pairs
   ParsePairs(CustomPairs);

   // Resize arrays
   ArrayResize(g_ccsData,         g_totalPairs);
   ArrayResize(g_lastAlertSignal, g_totalPairs);
   ArrayResize(g_lastAlertTime,   g_totalPairs);

   for(int i = 0; i < g_totalPairs; i++)
   {
      g_ccsData[i].pair          = g_pairs[i];
      g_ccsData[i].prevSignal    = 0;
      g_ccsData[i].signal        = 0;
      g_ccsData[i].lastEntryTime = 0;
      g_lastAlertSignal[i]       = "";
      g_lastAlertTime[i]         = 0;
   }

   g_trailCount = 0;

   CreateDashboard();
   EventSetTimer(1);

   Print("CCS Dashboard v2.00 initialized. Pairs: ", g_totalPairs);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| DEINIT                                                            |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   DeleteAllObjects();
   Print("CCS Dashboard v2.00 removed.");
}

//+------------------------------------------------------------------+
//| PARSE PAIRS dari string input                                     |
//+------------------------------------------------------------------+
void ParsePairs(string src)
{
   // Bersihkan spasi
   StringTrimLeft(src);
   StringTrimRight(src);

   // Hitung jumlah pair
   int count = 1;
   for(int i = 0; i < StringLen(src); i++)
      if(StringGetCharacter(src, i) == ',') count++;

   ArrayResize(g_pairs, count);

   int start = 0, idx = 0;
   for(int i = 0; i <= StringLen(src); i++)
   {
      if(i == StringLen(src) || StringGetCharacter(src, i) == ',')
      {
         if(i > start)
         {
            string p = StringSubstr(src, start, i - start);
            StringTrimLeft(p);
            StringTrimRight(p);
            if(StringLen(p) > 0 && idx < count)
               g_pairs[idx++] = p;
         }
         start = i + 1;
      }
   }

   g_totalPairs = idx;
   ArrayResize(g_pairs, g_totalPairs);
}

//+------------------------------------------------------------------+
//| ONTICK — hanya update jika bar baru                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Guard: hanya proses sekali per detik
   datetime now = TimeCurrent();
   if(now == g_lastUpdateTime) return;
   g_lastUpdateTime = now;
   g_updateCounter++;

   UpdateAllSignals();

   // Auto trade setiap 2 tick
   if(g_updateCounter % 2 == 0 && g_autoTradeON)
      RunAutoTrade();

   ManageTrailingStops();
   UpdateDashboard();
}

//+------------------------------------------------------------------+
//| ONTIMER — backup update jika tidak ada tick                       |
//+------------------------------------------------------------------+
void OnTimer()
{
   datetime now = TimeCurrent();
   if(now == g_lastUpdateTime) return;
   g_lastUpdateTime = now;
   g_updateCounter++;

   UpdateAllSignals();

   if(g_updateCounter % 2 == 0)
   {
      CheckAlerts();
      if(g_autoTradeON) RunAutoTrade();
   }

   ManageTrailingStops();
   UpdateDashboard();
}

//+------------------------------------------------------------------+
//| CHART EVENT — handle klik tombol                                  |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id != CHARTEVENT_OBJECT_CLICK) return;

   // Reset selected state
   ObjectSetInteger(0, sparam, OBJPROP_SELECTED, false);

   if(sparam == "AUTO")   { g_autoTradeON = !g_autoTradeON; ChartRedraw(); return; }
   if(sparam == "ALERT")  { g_alertON     = !g_alertON;     ChartRedraw(); return; }

   if(sparam == "HeaderCloseAll") { CloseAllPositions(); ChartRedraw(); return; }

   if(sparam == "F-") { ResizeFont(g_runtimeFontSize - 1); return; }
   if(sparam == "F+") { ResizeFont(g_runtimeFontSize + 1); return; }

   if(sparam == "HDR_RSI")  { tog_RSI  = !tog_RSI;  UpdateHeaderColors(); ChartRedraw(); return; }
   if(sparam == "HDR_SnR")  { tog_SnR  = !tog_SnR;  UpdateHeaderColors(); ChartRedraw(); return; }
   if(sparam == "HDR_ATR")  { tog_VOL  = !tog_VOL;  UpdateHeaderColors(); ChartRedraw(); return; }
   if(sparam == "HDR_BB")   { tog_BB   = !tog_BB;   UpdateHeaderColors(); ChartRedraw(); return; }
   if(sparam == "HDR_WARN") { tog_WARN = !tog_WARN; UpdateHeaderColors(); ChartRedraw(); return; }

   if(sparam == "M1") { if(g_runtimeMaxPos > 1) g_runtimeMaxPos--; ObjectSetString(0, "L1", OBJPROP_TEXT, IntegerToString(g_runtimeMaxPos)); return; }
   if(sparam == "M2") { if(g_runtimeMaxPos < 10) g_runtimeMaxPos++; ObjectSetString(0, "L1", OBJPROP_TEXT, IntegerToString(g_runtimeMaxPos)); return; }

   // Tombol Buy per pair
   if(StringFind(sparam, "BK_") == 0)
   {
      int i = (int)StringToInteger(StringSubstr(sparam, 3));
      if(i >= 0 && i < g_totalPairs) OpenTrade(g_pairs[i], OP_BUY);
      ChartRedraw();
      return;
   }

   // Tombol Sell per pair
   if(StringFind(sparam, "BS_") == 0)
   {
      int i = (int)StringToInteger(StringSubstr(sparam, 3));
      if(i >= 0 && i < g_totalPairs) OpenTrade(g_pairs[i], OP_SELL);
      ChartRedraw();
      return;
   }

   // Tombol Close per pair
   if(StringFind(sparam, "BX_") == 0)
   {
      int i = (int)StringToInteger(StringSubstr(sparam, 3));
      if(i >= 0 && i < g_totalPairs) CloseSymbol(g_pairs[i]);
      ChartRedraw();
      return;
   }
}

//+------------------------------------------------------------------+
//| RESIZE FONT                                                       |
//+------------------------------------------------------------------+
void ResizeFont(int newSize)
{
   if(newSize < 6 || newSize > 22) return;
   g_runtimeFontSize = newSize;
   DeleteAllObjects();
   CreateDashboard();
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| UPDATE WARNA HEADER TOGGLE                                        |
//+------------------------------------------------------------------+
void UpdateHeaderColors()
{
   ObjectSetInteger(0, "HDR_RSI",  OBJPROP_COLOR, tog_RSI  ? clrYellow : clrDimGray);
   ObjectSetInteger(0, "HDR_SnR",  OBJPROP_COLOR, tog_SnR  ? clrYellow : clrDimGray);
   ObjectSetInteger(0, "HDR_ATR",  OBJPROP_COLOR, tog_VOL  ? clrYellow : clrDimGray);
   ObjectSetInteger(0, "HDR_BB",   OBJPROP_COLOR, tog_BB   ? clrYellow : clrDimGray);
   ObjectSetInteger(0, "HDR_WARN", OBJPROP_COLOR, tog_WARN ? clrYellow : clrDimGray);
}

//+------------------------------------------------------------------+
//| CURRENCY STRENGTH — Multi-Timeframe (D1 + H4)                    |
//+------------------------------------------------------------------+
void CalcCurrencyStrength()
{
   // 28 pair standar
   string p[28] = {
      "GBPUSD","USDCHF","EURUSD","USDJPY","USDCAD","NZDUSD","AUDUSD",
      "AUDNZD","AUDCAD","AUDCHF","AUDJPY","CADJPY","CHFJPY","EURGBP",
      "EURAUD","EURCHF","EURJPY","EURNZD","EURCAD","GBPCHF","GBPAUD",
      "GBPCAD","GBPJPY","GBPNZD","NZDJPY","NZDCAD","CHFCAD","NZDCHF"
   };

   double scoreD1[28], scoreH4[28];

   // Hitung score D1 dan H4
   for(int i = 0; i < 28; i++)
   {
      scoreD1[i] = CalcPairScore(p[i], PERIOD_D1);
      scoreH4[i] = CalcPairScore(p[i], PERIOD_H4);
   }

   // Bobot: D1 = 60%, H4 = 40%
   double s[28];
   for(int i = 0; i < 28; i++)
      s[i] = (scoreD1[i] >= 0 && scoreH4[i] >= 0)
             ? scoreD1[i] * 0.6 + scoreH4[i] * 0.4
             : (scoreD1[i] >= 0 ? scoreD1[i] : scoreH4[i]);

   // Agregasi per mata uang (sama seperti v1 tapi pakai s[] gabungan)
   double su[8];
   su[0] = ((9-s[0]) + s[1] + (9-s[2]) + s[3] + s[4] + (9-s[5]) + (9-s[6])) / 7.0; // USD
   su[1] = (s[2] + s[13] + s[14] + s[15] + s[16] + s[17] + s[18]) / 7.0;             // EUR
   su[2] = (s[0] + (9-s[13]) + s[19] + s[20] + s[21] + s[22] + s[23]) / 7.0;         // GBP
   su[3] = ((9-s[1]) + (9-s[9]) + s[12] + (9-s[15]) + (9-s[19]) + s[26] + (9-s[27])) / 7.0; // CHF
   su[4] = ((9-s[4]) + (9-s[8]) + s[11] + (9-s[18]) + (9-s[21]) + (9-s[25]) + (9-s[26])) / 7.0; // CAD
   su[5] = (s[6] + s[7] + s[8] + s[9] + s[10] + (9-s[14]) + (9-s[20])) / 7.0;       // AUD
   su[6] = ((9-s[3]) + (9-s[10]) + (9-s[11]) + (9-s[12]) + (9-s[16]) + (9-s[22]) + (9-s[24])) / 7.0; // JPY
   su[7] = (s[5] + (9-s[7]) + (9-s[17]) + (9-s[23]) + s[24] + s[25] + s[27]) / 7.0; // NZD

   for(int i = 0; i < 8; i++)
      g_ccyStrength[i] = su[i];
}

// Hitung score 0-9 untuk satu pair pada satu timeframe
double CalcPairScore(string sym, int tf)
{
   double dc = iClose(sym, tf, 0);
   double dh = iHigh(sym,  tf, 0);
   double dl = iLow(sym,   tf, 0);

   if(dh <= dl || dc <= 0) return -1; // data tidak valid

   double ratio = (dc - dl) / (dh - dl);

   if(ratio >= 0.97) return 9;
   if(ratio >= 0.90) return 8;
   if(ratio >= 0.75) return 7;
   if(ratio >= 0.60) return 6;
   if(ratio >= 0.50) return 5;
   if(ratio >= 0.40) return 4;
   if(ratio >= 0.25) return 3;
   if(ratio >= 0.10) return 2;
   if(ratio >= 0.03) return 1;
   return 0;
}

// Ambil GAP kekuatan mata uang untuk satu pair
double GetCurrencyGap(string sym)
{
   string base = "", quote = "";

   if(sym == "XAUUSD") { base = "XAU"; quote = "USD"; }
   else if(StringLen(sym) == 6)
   {
      base  = StringSubstr(sym, 0, 3);
      quote = StringSubstr(sym, 3, 3);
   }
   else return 0;

   int bi = CurrencyIndex(base);
   int qi = CurrencyIndex(quote);
   if(bi < 0 || qi < 0) return 0;

   return NormalizeDouble(g_ccyStrength[bi] - g_ccyStrength[qi], 1);
}

//+------------------------------------------------------------------+
//| UPDATE SEMUA SINYAL                                               |
//+------------------------------------------------------------------+
void UpdateAllSignals()
{
   CalcCurrencyStrength();

   for(int i = 0; i < g_totalPairs; i++)
   {
      int rawSig = CalcSignal(g_pairs[i], i);
      int prev   = g_ccsData[i].prevSignal;
      int out    = rawSig;

      // Filter flip sinyal yang terlalu cepat (hysteresis)
      if(prev >=  2 && rawSig <= -1) out = 0;
      if(prev <= -2 && rawSig >=  1) out = 0;
      if(prev >=  1 && rawSig <= -2) out = 0;
      if(prev <= -1 && rawSig >=  2) out = 0;
      if(prev ==  2 && rawSig ==  0) out = 1;
      if(prev == -2 && rawSig ==  0) out = -1;

      g_ccsData[i].prevSignal = out;
      g_ccsData[i].signal     = out;
   }
}

//+------------------------------------------------------------------+
//| HITUNG SINYAL UNTUK SATU PAIR                                     |
//+------------------------------------------------------------------+
int CalcSignal(string sym, int idx)
{
   // Validasi data market
   if(MarketInfo(sym, MODE_BID) <= 0) return 0;

   double close  = iClose(sym, PERIOD_H1, 0);
   double ema20  = iMA(sym, PERIOD_H1, EMA20_Period,  0, MODE_EMA, PRICE_CLOSE, 0);
   double ema50  = iMA(sym, PERIOD_H1, EMA50_Period,  0, MODE_EMA, PRICE_CLOSE, 0);
   double ema100 = iMA(sym, PERIOD_H1, EMA100_Period, 0, MODE_EMA, PRICE_CLOSE, 0);
   double ema200 = iMA(sym, PERIOD_H1, EMA200_Period, 0, MODE_EMA, PRICE_CLOSE, 0);

   double bbLow  = iBands(sym, PERIOD_H1, BB_Period, BB_Deviation, 0, PRICE_CLOSE, MODE_LOWER, 0);
   double bbHigh = iBands(sym, PERIOD_H1, BB_Period, BB_Deviation, 0, PRICE_CLOSE, MODE_UPPER, 0);

   double rsi    = iRSI(sym, PERIOD_H1, RSI_Period, PRICE_CLOSE, 0);
   double rsiPrev= iRSI(sym, PERIOD_H1, RSI_Period, PRICE_CLOSE, 1);

   double atr    = iATR(sym, PERIOD_H1, ATR_Period, 0);
   double atrPrev= iATR(sym, PERIOD_H1, ATR_Period, 10);

   double high   = iHigh(sym, PERIOD_H1, 0);
   double low    = iLow(sym,  PERIOD_H1, 0);

   // Simpan ke struct
   g_ccsData[idx].ccyGap      = GetCurrencyGap(sym);
   g_ccsData[idx].rsi         = rsi;
   g_ccsData[idx].atr         = atr;
   g_ccsData[idx].bbTouchLow  = (bbLow  > 0 && low  <= bbLow);
   g_ccsData[idx].bbTouchHigh = (bbHigh > 0 && high >= bbHigh);

   if(close == 0 || rsi == 0) return 0;

   // --- EMA Gates ---
   int gateBull = 0, gateBear = 0;
   if(ema20  > 0) { if(close > ema20)  gateBull++; else gateBear++; }
   if(ema50  > 0) { if(close > ema50)  gateBull++; else gateBear++; }
   if(ema100 > 0) { if(close > ema100) gateBull++; else gateBear++; }
   if(ema200 > 0) { if(close > ema200) gateBull++; else gateBear++; }

   g_ccsData[idx].gateBull = gateBull;
   g_ccsData[idx].gateBear = gateBear;

   // --- Support & Resistance (H1 + H4 untuk robustness) ---
   double nearSupport = 0, nearResist = 0;
   double nearSupDist = 999999, nearResDist = 999999;
   FindSnR(sym, PERIOD_H1, close, atr, nearSupport, nearResist, nearSupDist, nearResDist);

   // Cek juga H4 SnR
   double supH4 = 0, resH4 = 0, supDistH4 = 999999, resDistH4 = 999999;
   FindSnR(sym, PERIOD_H4, close, atr, supH4, resH4, supDistH4, resDistH4);

   // Ambil yang lebih dekat
   if(supDistH4 < nearSupDist) { nearSupport = supH4; nearSupDist = supDistH4; }
   if(resDistH4 < nearResDist) { nearResist  = resH4; nearResDist = resDistH4; }

   double atrSafe = (atr > 0) ? atr : 1.0;
   bool nearSup = (nearSupport > 0 && nearSupDist < atrSafe * 1.5);
   bool nearRes = (nearResist  > 0 && nearResDist < atrSafe * 1.5);

   g_ccsData[idx].snrDist = nearSup ? nearSupDist / atrSafe
                          : nearRes ? nearResDist / atrSafe
                          : 999;

   // --- ATR Regime ---
   bool atrRising  = (atrPrev > 0 && atr > atrPrev);
   bool atrFalling = (atrPrev > 0 && atr < atrPrev);
   g_ccsData[idx].atrRising = atrRising;
   g_ccsData[idx].regime    = atrFalling ? "Sta" : (atrRising ? "Vol" : "=Nor");

   // --- RSI Conditions ---
   bool rsiOversold   = (rsi > 0 && rsi < RSI_Oversold);
   bool rsiOverbought = (rsi > RSI_Overbought);
   bool rsiTurningUp  = (rsi > rsiPrev && rsiPrev < RSI_Oversold);
   bool rsiTurningDn  = (rsi < rsiPrev && rsiPrev > RSI_Overbought);

   double gap    = g_ccsData[idx].ccyGap;
   bool gapBull  = (gap >  0.5);
   bool gapBear  = (gap < -0.5);

   int bullScore = 0, bearScore = 0;

   if(gapBull)
   {
      // GAP kontribusi
      bullScore += MathMax(0, (int)(gap - 3));

      // EMA Gates
      if(gateBull >= 4)      bullScore += 3;
      else if(gateBull >= 3) bullScore += 2;
      else if(gateBull >= 2) bullScore += 1;

      // RSI
      if(tog_RSI)
      {
         if(rsiOversold)   bullScore += 1;
         else if(rsiOverbought) bullScore -= 1;
         else if(rsiTurningUp)  bullScore += 1;
      }

      // BB
      if(tog_BB)
      {
         if(g_ccsData[idx].bbTouchLow)       bullScore += 1;
         else if(g_ccsData[idx].bbTouchHigh) bullScore -= 1;
      }

      // ATR
      if(tog_VOL)
      {
         if(atrFalling)      bullScore += 1;
         else if(atrRising)  bullScore -= 1;
      }

      // SnR
      if(tog_SnR)
      {
         if(nearSup)      bullScore += 1;
         else if(nearRes) bullScore -= 1;
      }

      // Kontradiksi EMA
      if(gateBear > gateBull) bullScore -= 2;
   }
   else if(gapBear)
   {
      bearScore += MathMax(0, (int)(MathAbs(gap) - 3));

      if(gateBear >= 4)      bearScore += 3;
      else if(gateBear >= 3) bearScore += 2;
      else if(gateBear >= 2) bearScore += 1;

      if(tog_RSI)
      {
         if(rsiOverbought)  bearScore += 1;
         else if(rsiOversold)   bearScore -= 1;
         else if(rsiTurningDn)  bearScore += 1;
      }

      if(tog_BB)
      {
         if(g_ccsData[idx].bbTouchHigh)     bearScore += 1;
         else if(g_ccsData[idx].bbTouchLow) bearScore -= 1;
      }

      if(tog_VOL)
      {
         if(atrFalling)      bearScore += 1;
         else if(atrRising)  bearScore -= 1;
      }

      if(tog_SnR)
      {
         if(nearRes)      bearScore += 1;
         else if(nearSup) bearScore -= 1;
      }

      if(gateBull > gateBear) bearScore -= 2;
   }
   else
   {
      g_ccsData[idx].warning = "";
      g_ccsData[idx].score   = 0;
      return 0;
   }

   // --- Warning ---
   string warn = "";
   if(atrRising && rsi > 70)                              warn = "VolTop";
   else if(atrRising && rsi < 30)                         warn = "VolBot";
   else if(g_ccsData[idx].bbTouchHigh && rsiOverbought)   warn = "OB+BB";
   else if(g_ccsData[idx].bbTouchLow  && rsiOversold)     warn = "OS+BB";
   else if(nearRes && gateBull >= 3)                       warn = "~Res";
   else if(nearSup && gateBear >= 3)                       warn = "~Sup";
   else if(atrPrev > 0 && atr > atrPrev * 1.5)            warn = "ATR+";

   g_ccsData[idx].warning = warn;

   // Warning penalty
   if(tog_WARN)
   {
      if(warn == "VolTop" || warn == "OB+BB") bullScore -= 2;
      else if(warn == "VolBot" || warn == "OS+BB") bearScore -= 2;
      else if(warn == "~Res")  bullScore -= 1;
      else if(warn == "~Sup")  bearScore -= 1;
      else if(warn == "ATR+") { bullScore -= 1; bearScore -= 1; }
   }

   g_ccsData[idx].score = (bullScore > bearScore) ? bullScore
                        : (bearScore > bullScore) ? -bearScore : 0;

   if(bullScore >= 7) return  2;
   if(bullScore >= 4) return  1;
   if(bearScore >= 7) return -2;
   if(bearScore >= 4) return -1;
   return 0;
}

//+------------------------------------------------------------------+
//| DETEKSI SUPPORT & RESISTANCE (swing high/low)                    |
//+------------------------------------------------------------------+
void FindSnR(string sym, int tf, double close, double atr,
             double &outSup, double &outRes,
             double &outSupDist, double &outResDist)
{
   outSup = 0; outRes = 0;
   outSupDist = 999999; outResDist = 999999;

   int bars = MathMin(300, iBars(sym, tf));
   if(bars < SnR_BarsLeft + SnR_BarsRight + 1) return;

   for(int b = SnR_BarsLeft; b < bars - SnR_BarsRight; b++)
   {
      double sh = iHigh(sym, tf, b);
      double sl = iLow(sym,  tf, b);
      bool isSH = true, isSL = true;

      for(int j = 1; j <= SnR_BarsLeft; j++)
      {
         if(sh <= iHigh(sym, tf, b + j)) isSH = false;
         if(sl >= iLow(sym,  tf, b + j)) isSL = false;
      }
      for(int j = 1; j <= SnR_BarsRight; j++)
      {
         if(sh <= iHigh(sym, tf, b - j)) isSH = false;
         if(sl >= iLow(sym,  tf, b - j)) isSL = false;
      }

      if(isSH == isSL) continue;

      if(isSH)
      {
         double dist = MathAbs(sh - close);
         if(close < sh && dist < outResDist) { outRes = sh; outResDist = dist; }
      }
      if(isSL)
      {
         double dist = MathAbs(sl - close);
         if(close > sl && dist < outSupDist) { outSup = sl; outSupDist = dist; }
      }
   }
}

//+------------------------------------------------------------------+
//| ALERT SYSTEM                                                      |
//+------------------------------------------------------------------+
void CheckAlerts()
{
   if(!g_alertON) return;

   for(int i = 0; i < g_totalPairs; i++)
   {
      int sig = g_ccsData[i].signal;
      if(sig == 0) continue;

      string sigStr = (sig ==  2) ? "STRONG BUY"
                    : (sig ==  1) ? "BUY"
                    : (sig == -1) ? "SELL"
                    : "STRONG SELL";

      // Hanya alert jika sinyal berubah dan belum alert dalam 5 menit
      datetime now = TimeCurrent();
      bool signalChanged = (sigStr != g_lastAlertSignal[i]);
      bool cooldownPassed = (now - g_lastAlertTime[i] > 300);

      if(signalChanged && cooldownPassed)
      {
         string msg = "CCS v2 | " + g_pairs[i] + " → " + sigStr;
         if(StringLen(g_ccsData[i].warning) > 0)
            msg += " [WARN: " + g_ccsData[i].warning + "]";

         Alert(msg);
         g_lastAlertSignal[i] = sigStr;
         g_lastAlertTime[i]   = now;
      }
   }
}

//+------------------------------------------------------------------+
//| AUTO TRADE                                                        |
//+------------------------------------------------------------------+
void RunAutoTrade()
{
   // Cek drawdown guard dulu
   if(!IsDrawdownOK())
   {
      // Tampilkan warning di chart
      ObjectSetString(0, "L_DDWarn", OBJPROP_TEXT, "DD LIMIT!");
      return;
   }

   for(int i = 0; i < g_totalPairs; i++)
   {
      int sig = g_ccsData[i].signal;
      if(sig != 2 && sig != -2) continue;

      int direction  = (sig ==  2) ? OP_BUY  : OP_SELL;
      int opposite   = (sig ==  2) ? OP_SELL : OP_BUY;

      // Cek cooldown — jangan entry terlalu sering
      datetime now = TimeCurrent();
      int barSeconds = PeriodSeconds(PERIOD_H1);
      if(now - g_ccsData[i].lastEntryTime < barSeconds * AutoTrade_CooldownBars)
         continue;

      // Cek spread
      if(!IsSpreadOK(g_pairs[i])) continue;

      // Tutup posisi berlawanan jika ada
      bool hasOpposite = false;
      for(int j = 0; j < OrdersTotal(); j++)
      {
         if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
         if(OrderSymbol() != g_pairs[i] || OrderMagicNumber() != MagicNumber) continue;
         if(OrderType() == opposite) { hasOpposite = true; break; }
      }
      if(hasOpposite) CloseSymbol(g_pairs[i]);

      // Buka posisi baru
      OpenTrade(g_pairs[i], direction);
      g_ccsData[i].lastEntryTime = now;
   }
}

//+------------------------------------------------------------------+
//| BUKA POSISI                                                       |
//+------------------------------------------------------------------+
void OpenTrade(string sym, int type)
{
   if(!IsTradeAllowed()) return;
   if(!SymbolSelect(sym, true)) return;

   // Cek spread
   if(!IsSpreadOK(sym))
   {
      Print("CCS v2: Spread terlalu lebar untuk ", sym, " — skip entry");
      return;
   }

   // Cek drawdown
   if(!IsDrawdownOK())
   {
      Print("CCS v2: Drawdown limit tercapai — trading dihentikan");
      return;
   }

   // Hitung jumlah posisi terbuka (semua pair)
   int openCount = 0;
   for(int j = 0; j < OrdersTotal(); j++)
   {
      if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() == MagicNumber &&
         (OrderType() == OP_BUY || OrderType() == OP_SELL))
         openCount++;
   }
   if(openCount >= g_runtimeMaxPos) return;

   // Cek apakah sudah ada posisi yang sama di pair ini
   for(int j = 0; j < OrdersTotal(); j++)
   {
      if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() == sym && OrderMagicNumber() == MagicNumber && OrderType() == type)
         return;
   }

   double ask   = MarketInfo(sym, MODE_ASK);
   double bid   = MarketInfo(sym, MODE_BID);
   if(ask <= 0 || bid <= 0) return;

   double atr   = iATR(sym, PERIOD_H1, ATR_Period, 0);
   double price = (type == OP_BUY) ? ask : bid;
   double sl    = 0, tp = 0;

   if(atr > 0)
   {
      sl = (type == OP_BUY) ? price - atr * ATR_SL_Mult : price + atr * ATR_SL_Mult;
      tp = (type == OP_BUY) ? price + atr * ATR_TP_Mult : price - atr * ATR_TP_Mult;

      int digits = (int)MarketInfo(sym, MODE_DIGITS);
      sl = NormalizeDouble(sl, digits);
      tp = NormalizeDouble(tp, digits);
   }

   // Hitung lot berdasarkan risk %
   double slPoints = (atr > 0) ? atr * ATR_SL_Mult : 0;
   //double lot      = CalcLotByRisk(sym, slPoints);

   // Coba kirim order
   int ticket = OrderSend(sym, type, lot, price, Slippage, sl, tp, "CCS_v2", MagicNumber, 0, clrNONE);

   if(ticket <= 0)
   {
      int err = GetLastError();
      Print("CCS v2: OrderSend gagal untuk ", sym, " Error: ", err);

      // Fallback: kirim tanpa SL/TP, lalu modify
      ticket = OrderSend(sym, type, lot, price, Slippage, 0, 0, "CCS_v2", MagicNumber, 0, clrNONE);
      if(ticket > 0 && atr > 0 && OrderSelect(ticket, SELECT_BY_TICKET))
      {
         int digits = (int)MarketInfo(sym, MODE_DIGITS);
         double openPrice = OrderOpenPrice();
         sl = (type == OP_BUY) ? openPrice - atr * ATR_SL_Mult : openPrice + atr * ATR_SL_Mult;
         tp = (type == OP_BUY) ? openPrice + atr * ATR_TP_Mult : openPrice - atr * ATR_TP_Mult;
         OrderModify(ticket, openPrice, NormalizeDouble(sl, digits), NormalizeDouble(tp, digits), 0, clrNONE);
      }
   }

   if(ticket > 0)
      Print("CCS v2: Order terbuka — ", sym, " ", (type == OP_BUY ? "BUY" : "SELL"),
            " Lot:", lot, " SL:", sl, " TP:", tp);
}

//+------------------------------------------------------------------+
//| TUTUP SEMUA POSISI UNTUK SATU PAIR                                |
//+------------------------------------------------------------------+
void CloseSymbol(string sym)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != sym || OrderMagicNumber() != MagicNumber) continue;

      double closePrice;
      color  arrowColor;

      if(OrderType() == OP_BUY)
      {
         closePrice = MarketInfo(sym, MODE_BID);
         arrowColor = clrRed;
      }
      else
      {
         closePrice = MarketInfo(sym, MODE_ASK);
         arrowColor = clrBlue;
      }

      bool closed = OrderClose(OrderTicket(), OrderLots(), closePrice, Slippage, arrowColor);
      if(closed) RemoveTrailData(OrderTicket());
      else Print("CCS v2: Gagal tutup order ", OrderTicket(), " Error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| TUTUP SEMUA POSISI                                                |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;

      double closePrice;
      color  arrowColor;

      if(OrderType() == OP_BUY)
      {
         closePrice = MarketInfo(OrderSymbol(), MODE_BID);
         arrowColor = clrRed;
      }
      else
      {
         closePrice = MarketInfo(OrderSymbol(), MODE_ASK);
         arrowColor = clrBlue;
      }

      OrderClose(OrderTicket(), OrderLots(), closePrice, Slippage, arrowColor);
   }
}

//+------------------------------------------------------------------+
//| HAPUS DATA TRAIL UNTUK TICKET TERTENTU                            |
//+------------------------------------------------------------------+
void RemoveTrailData(int ticket)
{
   for(int t = g_trailCount - 1; t >= 0; t--)
   {
      if(g_trailData[t].ticket == ticket)
      {
         for(int k = t; k < g_trailCount - 1; k++)
            g_trailData[k] = g_trailData[k + 1];
         g_trailCount--;
         break;
      }
   }
}

//+------------------------------------------------------------------+
//| TRAILING STOP BERBASIS ATR                                        |
//+------------------------------------------------------------------+
void ManageTrailingStops()
{
   // Bersihkan trail data untuk order yang sudah tutup
   for(int t = g_trailCount - 1; t >= 0; t--)
   {
      bool found = false;
      for(int j = 0; j < OrdersTotal(); j++)
      {
         if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
         if(OrderTicket() == g_trailData[t].ticket) { found = true; break; }
      }
      if(!found) RemoveTrailData(g_trailData[t].ticket);
   }

   // Update trailing untuk setiap posisi terbuka
   for(int j = 0; j < OrdersTotal(); j++)
   {
      if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      if(OrderType() != OP_BUY && OrderType() != OP_SELL) continue;

      string sym  = OrderSymbol();
      double atrH = iATR(sym, PERIOD_H1, ATR_Period, 0);
      if(atrH <= 0) continue;

      bool   isBuy     = (OrderType() == OP_BUY);
      double curPrice  = isBuy ? MarketInfo(sym, MODE_BID)
                               : MarketInfo(sym, MODE_ASK);
      double openPrice = OrderOpenPrice();
      double curSL     = OrderStopLoss();
      double profit    = isBuy ? (curPrice - openPrice) : (openPrice - curPrice);
      int    digits    = (int)MarketInfo(sym, MODE_DIGITS);

      // Cari atau buat trail data
      int ti = -1;
      for(int t = 0; t < g_trailCount; t++)
         if(g_trailData[t].ticket == OrderTicket()) { ti = t; break; }

      if(ti < 0)
      {
         if(g_trailCount >= MAX_TRAIL)
         {
            Print("CCS v2: TrailData penuh (MAX_TRAIL=", MAX_TRAIL, ")");
            continue;
         }
         ti = g_trailCount;
         g_trailData[ti].ticket = OrderTicket();
         g_trailData[ti].peak   = curPrice;
         g_trailData[ti].active = false;
         g_trailCount++;
      }

      // Update peak
      if(isBuy)  { if(curPrice > g_trailData[ti].peak) g_trailData[ti].peak = curPrice; }
      else       { if(curPrice < g_trailData[ti].peak) g_trailData[ti].peak = curPrice; }

      // Aktifkan trailing setelah profit >= 1x ATR
      if(!g_trailData[ti].active && profit >= atrH * TRAIL_ACTIVATE)
         g_trailData[ti].active = true;

      if(!g_trailData[ti].active) continue;

      // Hitung SL baru
      double newSL;
      int    stopLevel = (int)MarketInfo(sym, MODE_STOPLEVEL);
      double symPoint  = MarketInfo(sym, MODE_POINT);

      if(isBuy)
      {
         newSL = g_trailData[ti].peak - atrH * TRAIL_ATR_MULT;
         // Pastikan SL tidak lebih rendah dari SL lama dan tidak terlalu dekat harga
         if(newSL > curSL + atrH * 0.2 || curSL == 0)
         {
            newSL = NormalizeDouble(newSL, digits);
            double minSL = curPrice - stopLevel * symPoint;
            if(newSL < minSL) newSL = minSL;
            OrderModify(OrderTicket(), openPrice, newSL, OrderTakeProfit(), 0, clrWhite);
         }
      }
      else
      {
         newSL = g_trailData[ti].peak + atrH * TRAIL_ATR_MULT;
         if(newSL < curSL - atrH * 0.2 || curSL == 0)
         {
            newSL = NormalizeDouble(newSL, digits);
            double maxSL = curPrice + stopLevel * symPoint;
            if(newSL > maxSL) newSL = maxSL;
            OrderModify(OrderTicket(), openPrice, newSL, OrderTakeProfit(), 0, clrWhite);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| BUAT DASHBOARD                                                    |
//+------------------------------------------------------------------+
void CreateDashboard()
{
   int x   = StartX;
   int y   = StartY;
   int fs  = g_runtimeFontSize;
   int lh  = (int)(fs * 1.8 + 1); // line height
   double cs = (double)fs / 8.0;
   if(cs < 1.0) cs = 1.0;

   // Definisi kolom
   int c0    = x;
   int c1    = c0   + (int)(45 * cs);  // PL
   int c2    = c1   + (int)(50 * cs);  // SIG
   int cPct  = c2   + (int)(55 * cs);  // %
   int c4    = cPct + (int)(28 * cs);  // GAP
   int c5    = c4   + (int)(45 * cs);  // GT
   int c6    = c5   + (int)(45 * cs);  // RSI
   int cSnR  = c6   + (int)(45 * cs);  // SnR
   int cATR  = cSnR + (int)(40 * cs);  // ATR
   int cBB   = cATR + (int)(75 * cs);  // BB
   int cWarn = cBB  + (int)(35 * cs);  // WARN
   int cB    = cWarn+ (int)(50 * cs);  // Buy btn
   int cS    = cB   + (int)(28 * cs);  // Sell btn
   int cX    = cS   + (int)(28 * cs);  // Close btn
   int totalW= cX   + (int)(40 * cs);
   int btnH  = MathMax(12, lh - 2);

   // --- Header Row ---
   int hy = y;
   CreateLabel("H_Pair",   "PR",  c0,   hy, HeaderColor,    fs);
   CreateLabel("H_Profit", "PL",  c1,   hy, HeaderColor,    fs);
   CreateLabel("H_Signal", "SIG", c2,   hy, HeaderColor,    fs);
   CreateLabel("H_Pct",    "%",   cPct, hy, clrDodgerBlue,  fs);
   CreateLabel("H_Gap",    "GAP", c4,   hy, HeaderColor,    fs);
   CreateLabel("H_Gates",  "GT",  c5,   hy, HeaderColor,    fs);

   CreateToggleHeader("HDR_RSI",  "RSI", c6,   hy, (int)(45*cs), lh, fs, tog_RSI);
   CreateToggleHeader("HDR_SnR",  "SnR", cSnR, hy, (int)(40*cs), lh, fs, tog_SnR);
   CreateToggleHeader("HDR_ATR",  "ATR", cATR, hy, (int)(35*cs), lh, fs, tog_VOL);
   CreateToggleHeader("HDR_BB",   "BB",  cBB,  hy, (int)(35*cs), lh, fs, tog_BB);
   CreateToggleHeader("HDR_WARN", "WN",  cWarn,hy, (int)(40*cs), lh, fs, tog_WARN);

   CreateButton("HeaderCloseAll", "X", cB, hy - 2, (int)(80*cs), 18, clrGray, clrBlack);

   y += lh + 5;

   // --- Baris per pair ---
   for(int i = 0; i < g_totalPairs; i++)
   {
      int ry = y + i * lh;
      int ly = ry + 1;
      string si = IntegerToString(i);

      // Background row
      string bgName = "RBG_" + si;
      if(ObjectFind(0, bgName) < 0)
         ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE,   x);
      ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE,   ry);
      ObjectSetInteger(0, bgName, OBJPROP_XSIZE,       totalW);
      ObjectSetInteger(0, bgName, OBJPROP_YSIZE,       lh - 1);
      ObjectSetInteger(0, bgName, OBJPROP_CORNER,      CORNER_LEFT_UPPER);
      ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR,     MakeRGB(35, 35, 35));
      ObjectSetInteger(0, bgName, OBJPROP_BORDER_COLOR,MakeRGB(50, 50, 50));
      ObjectSetInteger(0, bgName, OBJPROP_BACK,        true);
      ObjectSetInteger(0, bgName, OBJPROP_SELECTABLE,  false);
      ObjectSetInteger(0, bgName, OBJPROP_HIDDEN,      true);

      // Labels
      CreateLabel("PR_" + si, g_pairs[i], c0,   ly, TextColor, fs);
      CreateLabel("PL_" + si, "--",        c1,   ly, clrGray,   fs);
      CreateLabel("SG_" + si, "WAIT",      c2,   ly, clrGray,   fs);
      CreateLabel("PC_" + si, "",          cPct, ly, clrGray,   fs);
      CreateLabel("GP_" + si, "--",        c4,   ly, clrGray,   fs);
      CreateLabel("GT_" + si, "--",        c5,   ly, clrGray,   fs);
      CreateLabel("RS_" + si, "--",        c6,   ly, clrGray,   fs);
      CreateLabel("SR_" + si, "--",        cSnR, ly, clrGray,   fs);
      CreateLabel("AV_" + si, "--",        cATR, ly, clrGray,   fs);
      CreateLabel("BB_" + si, "--",        cBB,  ly, clrGray,   fs);
      CreateLabel("WN_" + si, "",          cWarn,ly, clrGray,   fs);

      // Tombol aksi
      CreateButton("BK_" + si, "B",  cB, ry + 1, (int)(28*cs), btnH, clrForestGreen, clrWhite);
      CreateButton("BS_" + si, "S",  cS, ry + 1, (int)(28*cs), btnH, clrCrimson,     clrWhite);
      CreateButton("BX_" + si, "NO", cX, ry + 1, (int)(35*cs), btnH, clrGray,        clrBlack);
   }

   // --- Footer ---
   int bY = y + (g_totalPairs + 1) * lh;
   int bx = x;

   CreateLabel("L0", "MAX:", bx, bY, HeaderColor, fs);
   bx += (int)(30 * cs);
   CreateButton("M1", "-", bx, bY - 2, (int)(16*cs), (int)(14*cs), clrRed,  clrWhite);
   bx += (int)(18 * cs);
   CreateLabel("L1", IntegerToString(g_runtimeMaxPos), bx, bY, clrLime, fs);
   bx += (int)(20 * cs);
   CreateButton("M2", "+", bx, bY - 2, (int)(16*cs), (int)(14*cs), clrLime, clrBlack);
   bx += (int)(30 * cs);

   CreateLabel("L2", "BAL:", bx, bY, HeaderColor, fs);
   bx += (int)(30 * cs);
   CreateLabel("L3", "$0", bx, bY, clrLime, fs);
   bx += (int)(60 * cs);

   CreateLabel("L4", "MAR:", bx, bY, HeaderColor, fs);
   bx += (int)(30 * cs);
   CreateLabel("L5", "$0", bx, bY, clrLime, fs);
   bx += (int)(60 * cs);

   // Drawdown warning label
   CreateLabel("L_DDWarn", "", bx, bY, clrRed, fs);
   bx += (int)(70 * cs);

   CreateButton("F-",    "F-",   bx, bY - 2, (int)(20*cs), (int)(14*cs), clrGray,      clrWhite);
   bx += (int)(25 * cs);
   CreateLabel("L6", "F" + IntegerToString(g_runtimeFontSize), bx, bY, clrLightGray, fs);
   bx += (int)(25 * cs);
   CreateButton("F+",    "F+",   bx, bY - 2, (int)(20*cs), (int)(14*cs), clrLime,      clrBlack);
   bx += (int)(30 * cs);

   CreateButton("AUTO",  "A:OF", bx, bY - 2, (int)(65*cs), (int)(14*cs), C'50,50,50',  clrGray);
   bx += (int)(70 * cs);
   CreateButton("ALERT", "AL:ON",bx, bY - 2, (int)(65*cs), (int)(14*cs), C'0,100,0',   clrLime);
}

//+------------------------------------------------------------------+
//| BUAT TOGGLE HEADER BUTTON                                         |
//+------------------------------------------------------------------+
void CreateToggleHeader(string name, string text, int x, int y, int w, int h, int fs, bool isOn)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE,    x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE,    y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE,        w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE,        h);
   ObjectSetString(0,  name, OBJPROP_TEXT,         text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,        isOn ? clrYellow : clrDimGray);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR,      clrBlack);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, clrBlack);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,     fs);
   ObjectSetString(0,  name, OBJPROP_FONT,         "Consolas");
   ObjectSetInteger(0, name, OBJPROP_CORNER,       CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_BACK,         false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE,   true);
   ObjectSetInteger(0, name, OBJPROP_SELECTED,     false);
}

//+------------------------------------------------------------------+
//| UPDATE DASHBOARD                                                  |
//+------------------------------------------------------------------+
void UpdateDashboard()
{
   bool ddOK = IsDrawdownOK();

   for(int i = 0; i < g_totalPairs; i++)
   {
      string si = IntegerToString(i);

      // --- Sinyal ---
      int    sig = g_ccsData[i].signal;
      string sigText;
      color  sigColor;

      switch(sig)
      {
         case  2: sigText = "StrB"; sigColor = clrLime;           break;
         case  1: sigText = "Buy";  sigColor = clrMediumSeaGreen; break;
         case -1: sigText = "Sell"; sigColor = clrTomato;         break;
         case -2: sigText = "StrS"; sigColor = clrRed;            break;
         default: sigText = "Wait"; sigColor = clrGray;           break;
      }

      ObjectSetString(0,  "SG_" + si, OBJPROP_TEXT,  sigText);
      ObjectSetInteger(0, "SG_" + si, OBJPROP_COLOR, sigColor);

      // --- Score % ---
      int score  = g_ccsData[i].score;
      int dynMax = 9 + (tog_RSI ? 1 : 0) + (tog_SnR ? 1 : 0)
                     + (tog_VOL ? 1 : 0) + (tog_BB  ? 1 : 0);
      int pct    = (dynMax > 0) ? (int)(MathAbs(score) * 100 / dynMax) : 0;
      if(pct > 100) pct = 100;

      color pctColor = clrGray;
      if(score >=  7) pctColor = clrLime;
      else if(score >=  4) pctColor = clrMediumSeaGreen;
      else if(score <= -7) pctColor = clrRed;
      else if(score <= -4) pctColor = clrTomato;

      ObjectSetString(0,  "PC_" + si, OBJPROP_TEXT,  (pct > 0) ? IntegerToString(pct) + "%" : "");
      ObjectSetInteger(0, "PC_" + si, OBJPROP_COLOR, pctColor);

      // --- GAP ---
      double gap     = g_ccsData[i].ccyGap;
      color  gapColor = (gap >= CS_Strong_Threshold)  ? clrLime
                      : (gap <= -CS_Strong_Threshold) ? clrRed
                      : clrGray;
      ObjectSetString(0,  "GP_" + si, OBJPROP_TEXT,  DoubleToString(MathAbs(gap), 1));
      ObjectSetInteger(0, "GP_" + si, OBJPROP_COLOR, gapColor);

      // --- Gates ---
      int gb = g_ccsData[i].gateBull, gs = g_ccsData[i].gateBear;
      color gtColor = (gb > gs) ? clrMediumSeaGreen : (gs > gb) ? clrTomato : clrGray;
      ObjectSetString(0,  "GT_" + si, OBJPROP_TEXT,  IntegerToString(gb) + "/" + IntegerToString(gs));
      ObjectSetInteger(0, "GT_" + si, OBJPROP_COLOR, gtColor);

      // --- RSI ---
      double rsiVal = g_ccsData[i].rsi;
      color  rsiColor = tog_RSI
         ? ((rsiVal > 0 && rsiVal < RSI_Oversold) ? clrLime
         :  (rsiVal > RSI_Overbought)             ? clrRed
         :  clrWhite)
         : clrGray;
      ObjectSetString(0,  "RS_" + si, OBJPROP_TEXT,  DoubleToString(rsiVal, 1));
      ObjectSetInteger(0, "RS_" + si, OBJPROP_COLOR, rsiColor);

      // --- SnR ---
      double snrDist = g_ccsData[i].snrDist;
      string snrText = (snrDist > 0 && snrDist < 999) ? DoubleToString(snrDist, 1) : "-";
      color  snrColor = tog_SnR
         ? ((snrDist > 0 && snrDist < 1.5) ? clrMediumSeaGreen : clrWhite)
         : clrGray;
      ObjectSetString(0,  "SR_" + si, OBJPROP_TEXT,  snrText);
      ObjectSetInteger(0, "SR_" + si, OBJPROP_COLOR, snrColor);

      // --- ATR ---
      double atrVal = g_ccsData[i].atr;
      string atrText = (atrVal > 0)
         ? DoubleToString(atrVal, (int)MarketInfo(g_pairs[i], MODE_DIGITS))
           + (g_ccsData[i].atrRising ? "^" : "v")
         : "-";
      color atrColor = tog_VOL
         ? ((atrVal > 0) ? (g_ccsData[i].atrRising ? clrOrange : clrWhite) : clrGray)
         : clrGray;
      ObjectSetString(0,  "AV_" + si, OBJPROP_TEXT,  atrText);
      ObjectSetInteger(0, "AV_" + si, OBJPROP_COLOR, atrColor);

      // --- BB ---
      string bbText  = "M";
      color  bbColor = clrGray;
      if(g_ccsData[i].bbTouchLow)       { bbText = "L"; bbColor = clrLime; }
      else if(g_ccsData[i].bbTouchHigh) { bbText = "H"; bbColor = clrRed;  }
      ObjectSetString(0,  "BB_" + si, OBJPROP_TEXT,  bbText);
      ObjectSetInteger(0, "BB_" + si, OBJPROP_COLOR, tog_BB ? bbColor : clrGray);

      // --- Warning ---
      string warn = g_ccsData[i].warning;
      color  warnColor = clrGray;
      if(StringFind(warn, "Vol") == 0 || StringFind(warn, "OB+") == 0 || StringFind(warn, "OS+") == 0)
         warnColor = clrRed;
      else if(StringLen(warn) > 0)
         warnColor = clrOrange;
      ObjectSetString(0,  "WN_" + si, OBJPROP_TEXT,  warn);
      ObjectSetInteger(0, "WN_" + si, OBJPROP_COLOR, warnColor);

      // --- Profit & Close Button ---
      double profit = 0;
      int    openCount = 0;
      bool   hasBuy = false, hasSell = false;

      for(int j = 0; j < OrdersTotal(); j++)
      {
         if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
         if(OrderSymbol() != g_pairs[i] || OrderMagicNumber() != MagicNumber) continue;
         profit += OrderProfit() + OrderSwap() + OrderCommission();
         openCount++;
         if(OrderType() == OP_BUY)  hasBuy  = true;
         if(OrderType() == OP_SELL) hasSell = true;
      }

      string plText  = (openCount > 0) ? ((profit >= 0 ? "+" : "") + DoubleToString(profit, 2)) : "--";
      color  plColor = (openCount > 0) ? (profit >= 0 ? clrLime : clrRed) : clrGray;
      ObjectSetString(0,  "PL_" + si, OBJPROP_TEXT,  plText);
      ObjectSetInteger(0, "PL_" + si, OBJPROP_COLOR, plColor);

      string closeText  = "NO";
      color  closeBg    = clrGray;
      color  closeText2 = clrBlack;
      if(openCount > 0)
      {
         closeText  = (hasBuy && hasSell) ? "A" : hasBuy ? "B" : "S";
         closeBg    = (profit >= 0) ? clrLime : clrRed;
         closeText2 = (profit >= 0) ? clrBlack : clrWhite;
      }
      ObjectSetString(0,  "BX_" + si, OBJPROP_TEXT,    closeText);
      ObjectSetInteger(0, "BX_" + si, OBJPROP_BGCOLOR, closeBg);
      ObjectSetInteger(0, "BX_" + si, OBJPROP_COLOR,   closeText2);
   }

   // --- Footer: Total P/L, Balance, Margin ---
   double totalProfit = 0;
   int    totalOrders = 0;
   for(int j = 0; j < OrdersTotal(); j++)
   {
      if(!OrderSelect(j, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != MagicNumber) continue;
      totalProfit += OrderProfit() + OrderSwap() + OrderCommission();
      totalOrders++;
   }

   ObjectSetString(0, "L3", OBJPROP_TEXT, "$" + DoubleToString(AccountBalance(),    2));
   ObjectSetString(0, "L5", OBJPROP_TEXT, "$" + DoubleToString(AccountFreeMargin(), 2));

   string closeAllText  = (totalOrders > 0)
      ? ((totalProfit >= 0 ? "+" : "") + DoubleToString(totalProfit, 0)
         + "(" + IntegerToString(totalOrders) + "/" + IntegerToString(g_runtimeMaxPos) + ")")
      : "X";
   color closeAllBg   = (totalOrders > 0) ? (totalProfit >= 0 ? clrLime : clrRed) : clrGray;
   color closeAllText2= (totalOrders > 0) ? (totalProfit >= 0 ? clrBlack : clrWhite) : clrBlack;

   ObjectSetString(0,  "HeaderCloseAll", OBJPROP_TEXT,    closeAllText);
   ObjectSetInteger(0, "HeaderCloseAll", OBJPROP_BGCOLOR, closeAllBg);
   ObjectSetInteger(0, "HeaderCloseAll", OBJPROP_COLOR,   closeAllText2);

   // Drawdown warning
   if(!ddOK)
      ObjectSetString(0, "L_DDWarn", OBJPROP_TEXT, "⚠ DD LIMIT");
   else
      ObjectSetString(0, "L_DDWarn", OBJPROP_TEXT, "");

   // Auto/Alert buttons
   ObjectSetString(0,  "AUTO",  OBJPROP_TEXT,    g_autoTradeON ? "A:ON" : "A:OF");
   ObjectSetInteger(0, "AUTO",  OBJPROP_BGCOLOR, g_autoTradeON ? clrDarkGreen : C'50,50,50');
   ObjectSetInteger(0, "AUTO",  OBJPROP_COLOR,   g_autoTradeON ? clrLime : clrGray);

   ObjectSetString(0,  "ALERT", OBJPROP_TEXT,    g_alertON ? "AL:ON" : "AL:OF");
   ObjectSetInteger(0, "ALERT", OBJPROP_BGCOLOR, g_alertON ? C'0,100,0' : C'50,50,50');
   ObjectSetInteger(0, "ALERT", OBJPROP_COLOR,   g_alertON ? clrLime : clrGray);

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| BUAT LABEL                                                        |
//+------------------------------------------------------------------+
void CreateLabel(string name, string text, int x, int y, color clr, int fontSize)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0,  name, OBJPROP_TEXT,      text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,     clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,  fontSize);
   ObjectSetString(0,  name, OBJPROP_FONT,      "Consolas");
   ObjectSetInteger(0, name, OBJPROP_CORNER,    CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR,    ANCHOR_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| BUAT BUTTON                                                       |
//+------------------------------------------------------------------+
void CreateButton(string name, string text, int x, int y, int w, int h, color bgColor, color textColor)
{
   if(ObjectFind(0, name) < 0)
      ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);

   ObjectSetInteger(0, name, OBJPROP_XDISTANCE,    x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE,    y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE,        w);
   ObjectSetInteger(0, name, OBJPROP_YSIZE,        h);
   ObjectSetString(0,  name, OBJPROP_TEXT,         text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,        textColor);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR,      bgColor);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, clrGray);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,     g_runtimeFontSize);
   ObjectSetString(0,  name, OBJPROP_FONT,         "Consolas");
   ObjectSetInteger(0, name, OBJPROP_CORNER,       CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_BACK,         false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE,   true);
   ObjectSetInteger(0, name, OBJPROP_SELECTED,     false);
}

//+------------------------------------------------------------------+
//| HAPUS SEMUA OBJEK DASHBOARD                                       |
//+------------------------------------------------------------------+
void DeleteAllObjects()
{
   string prefixes[] = {
      "RBG_","PR_","PL_","SG_","PC_","GP_","GT_","RS_",
      "SR_","AV_","WN_","H_","BB_","BK_","BS_","BX_","HDR_","Header",
      "M1","M2","F-","F+","AUTO","ALERT","L"
   };

   for(int i = ObjectsTotal(-1) - 1; i >= 0; i--)
   {
      string name = ObjectName(i);
      for(int p = 0; p < ArraySize(prefixes); p++)
      {
         if(StringFind(name, prefixes[p]) == 0)
         {
            ObjectDelete(0, name);
            break;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| END OF FILE                                                       |
//+------------------------------------------------------------------+
