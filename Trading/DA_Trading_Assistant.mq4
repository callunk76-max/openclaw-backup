//+------------------------------------------------------------------+
//|                                      DA_Trading_Assistant.mq4    |
//|                                   Dwiyan Anggara Trading Style   |
//|                          Auto Lot Management & Order Assistant   |
//+------------------------------------------------------------------+
#property copyright "DA Trading Assistant - Reconstructed Logic"
#property version   "1.00"
#property strict
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//+------------------------------------------------------------------+
//| DA TRADING ASSISTANT                                             |
//|                                                                  |
//| Fitur:                                                           |
//| 1. AUTO LOT MANAGEMENT - Hitung lot berdasarkan balance & risk   |
//| 2. AUTO ORDER PLACEMENT - One-click BUY/SELL dengan SL/TP       |
//| 3. RISK/REWARD CALCULATOR - Hitung RR ratio otomatis            |
//| 4. MONEY MANAGEMENT - Risk % per trade & max drawdown           |
//| 5. POSITION SIZE CALCULATOR - Berdasarkan SL distance           |
//| 6. ACCOUNT INFO PANEL - Info balance, equity, margin dll        |
//+------------------------------------------------------------------+

// --- INPUT PARAMETERS ---
input string   ___MM___ = "==== MONEY MANAGEMENT ====";
input double   InpRiskPerTrade = 2.0;                  // Risk % per Trade
input double   InpMaxDailyLoss = 10.0;                 // Max Daily Loss %
input double   InpMaxDrawdown = 20.0;                  // Max Total Drawdown %
input bool     InpUseFixedLot = false;                 // Use Fixed Lot (instead of %)
input double   InpFixedLotSize = 0.01;                 // Fixed Lot Size

input string   ___SLTP___ = "==== SL/TP SETTINGS ====";
input bool     InpUseAutoSL = true;                    // Auto Calculate SL
input double   InpDefaultSLPips = 100.0;               // Default SL (pips)
input double   InpMinRR = 1.5;                         // Min Risk/Reward Ratio
input bool     InpUseATRSL = true;                     // Use ATR for SL
input double   InpATRMultiplier = 1.5;                 // ATR Multiplier for SL

input string   ___PANEL___ = "==== PANEL SETTINGS ====";
input int      InpPanelX = 10;                         // Panel X Offset
input int      InpPanelY = 10;                         // Panel Y Offset
input color    InpPanelBg = clrDarkSlateGray;          // Panel Background

input string   ___ADV___ = "==== ADVANCED ====";
input int      InpMagicNumber = 20242;                 // Magic Number
input bool     InpConfirmTrades = true;                // Confirm Before Trading
input bool     InpShowAlerts = true;                   // Show Trade Alerts

// --- GLOBAL VARIABLES ---
double g_currentATR;
double g_currentSpread;
double g_optimalLot;
double g_accountBalance;
double g_accountEquity;
double g_dailyProfitLoss = 0;
datetime g_lastDayChecked = 0;

// Chart objects
string PANEL_NAME = "DA_TradingAssistant_Panel";
string BTN_BUY = "DA_BTN_BUY";
string BTN_SELL = "DA_BTN_SELL";
string BTN_CLOSE = "DA_BTN_CLOSE";
string BTN_HALF = "DA_BTN_HALF";

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   // Create control panel
   DrawPanel();
   
   EventSetMillisecondTimer(500);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
int OnDeinit()
{
   // Remove all panel objects
   ObjectsDeleteAll(0, "DA_");
   EventKillTimer();
   
   return(0);
}

//+------------------------------------------------------------------+
//| Timer function - update panel periodically                       |
//+------------------------------------------------------------------+
void OnTimer()
{
   UpdatePanel();
   
   // Check for new day (reset daily P/L)
   MqlDateTime dt;
   TimeCurrent(dt);
   datetime currentDay = StringToTime(IntegerToString(dt.year) + "." + 
                                       IntegerToString(dt.mon) + "." + 
                                       IntegerToString(dt.day));
   if(currentDay != g_lastDayChecked)
   {
      g_lastDayChecked = currentDay;
      g_dailyProfitLoss = 0;
   }
   
   // Update daily P/L
   CalculateDailyPL();
}

//+------------------------------------------------------------------+
//| Chart event handler                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   if(id == CHARTEVENT_OBJECT_CLICK)
   {
      if(sparam == BTN_BUY)
      {
         if(InpConfirmTrades)
         {
            int msg = MessageBox("Place BUY order?\nLot: " + DoubleToStr(g_optimalLot, 2) +
                                 "\nSL: " + DoubleToStr(GetStopLoss(OP_BUY) / Point, 0) + " pips" +
                                 "\nRR: " + DoubleToStr(GetRR(OP_BUY), 2),
                                 "DA Trading Assistant", MB_YESNO | MB_ICONQUESTION);
            if(msg == IDYES) PlaceTrade(OP_BUY);
         }
         else
            PlaceTrade(OP_BUY);
            
         ChartRedraw();
      }
      
      if(sparam == BTN_SELL)
      {
         if(InpConfirmTrades)
         {
            int msg = MessageBox("Place SELL order?\nLot: " + DoubleToStr(g_optimalLot, 2) +
                                 "\nSL: " + DoubleToStr(GetStopLoss(OP_SELL) / Point, 0) + " pips" +
                                 "\nRR: " + DoubleToStr(GetRR(OP_SELL), 2),
                                 "DA Trading Assistant", MB_YESNO | MB_ICONQUESTION);
            if(msg == IDYES) PlaceTrade(OP_SELL);
         }
         else
            PlaceTrade(OP_SELL);
            
         ChartRedraw();
      }
      
      if(sparam == BTN_CLOSE)
      {
         CloseAllTrades();
         ChartRedraw();
      }
      
      if(sparam == BTN_HALF)
      {
         CloseHalfTrades();
         ChartRedraw();
      }
   }
}

//+------------------------------------------------------------------+
//| Draw the main control panel                                      |
//+------------------------------------------------------------------+
void DrawPanel()
{
   int x = InpPanelX;
   int y = InpPanelY;
   int w = 280;
   int lineH = 20;
   
   // Panel background
   ObjectCreate(0, PANEL_NAME, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_YSIZE, 240);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_BGCOLOR, InpPanelBg);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_COLOR, clrDimGray);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_BACK, false);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, PANEL_NAME, OBJPROP_HIDDEN, true);
   
   // Add panel label
   CreateLabel("DA_TITLE", x + 5, y + 2, "DA TRADING ASSISTANT v1.0", clrGold, 10, true);
   CreateLabel("DA_LINE1", x + 5, y + 22, "━━━━━━━━━━━━━━━━━━━━━━━━", clrDimGray, 8, false);
   
   // ---- SECTION 1: ACCOUNT INFO ----
   CreateLabel("DA_SEC1", x + 5, y + 38, "▶ ACCOUNT INFO", clrSkyBlue, 9, true);
   CreateLabel("DA_BAL",  x + 10, y + 56, "Balance:   --", clrWhite, 8, false);
   CreateLabel("DA_EQ",   x + 10, y + 72, "Equity:    --", clrWhite, 8, false);
   CreateLabel("DA_MARG", x + 140, y + 56, "Margin:    --", clrWhite, 8, false);
   CreateLabel("DA_FMARG", x + 140, y + 72, "Free Mrg:  --", clrWhite, 8, false);
   CreateLabel("DA_DAYPL", x + 10, y + 88, "Daily P/L: --", clrWhite, 8, false);
   CreateLabel("DA_TOTPL", x + 140, y + 88, "Total P/L: --", clrWhite, 8, false);
   
   // ---- SECTION 2: LOT CALCULATOR ----
   CreateLabel("DA_SEC2", x + 5, y + 108, "▶ LOT CALCULATOR", clrSkyBlue, 9, true);
   CreateLabel("DA_RISK", x + 10, y + 126, "Risk:      --%", clrWhite, 8, false);
   CreateLabel("DA_LOT",  x + 140, y + 126, "Lot:       --", clrLime, 9, true);
   CreateLabel("DA_SL",   x + 10, y + 142, "SL:        -- pips", clrWhite, 8, false);
   CreateLabel("DA_RR",   x + 140, y + 142, "RR:        --", clrWhite, 8, false);
   CreateLabel("DA_TP",   x + 10, y + 158, "TP:        -- pips", clrWhite, 8, false);
   
   // ---- SECTION 3: BUTTONS ----
   CreateLabel("DA_SEC3", x + 5, y + 178, "▶ QUICK ACTIONS", clrSkyBlue, 9, true);
   
   // BUY button
   ObjectCreate(0, BTN_BUY, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_XDISTANCE, x + 10);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_YDISTANCE, y + 195);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_XSIZE, 55);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_YSIZE, 30);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_BGCOLOR, clrGreen);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_COLOR, clrWhite);
   ObjectSetString(0, BTN_BUY, OBJPROP_TEXT, "BUY ▲");
   ObjectSetInteger(0, BTN_BUY, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, BTN_BUY, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   
   // SELL button
   ObjectCreate(0, BTN_SELL, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_XDISTANCE, x + 70);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_YDISTANCE, y + 195);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_XSIZE, 55);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_YSIZE, 30);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_BGCOLOR, clrRed);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_COLOR, clrWhite);
   ObjectSetString(0, BTN_SELL, OBJPROP_TEXT, "SELL ▼");
   ObjectSetInteger(0, BTN_SELL, OBJPROP_FONTSIZE, 9);
   ObjectSetInteger(0, BTN_SELL, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   
   // CLOSE ALL button
   ObjectCreate(0, BTN_CLOSE, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_XDISTANCE, x + 130);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_YDISTANCE, y + 195);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_XSIZE, 65);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_YSIZE, 30);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_BGCOLOR, clrDarkOrange);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_COLOR, clrWhite);
   ObjectSetString(0, BTN_CLOSE, OBJPROP_TEXT, "CLOSE ALL");
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, BTN_CLOSE, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   
   // CLOSE HALF button
   ObjectCreate(0, BTN_HALF, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_XDISTANCE, x + 200);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_YDISTANCE, y + 195);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_XSIZE, 65);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_YSIZE, 30);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_BGCOLOR, clrSteelBlue);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_COLOR, clrWhite);
   ObjectSetString(0, BTN_HALF, OBJPROP_TEXT, "CLOSE 1/2");
   ObjectSetInteger(0, BTN_HALF, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, BTN_HALF, OBJPROP_CORNER, CORNER_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| Update panel values                                              |
//+------------------------------------------------------------------+
void UpdatePanel()
{
   g_accountBalance = AccountBalance();
   g_accountEquity = AccountEquity();
   g_currentATR = iATR(NULL, 0, 14, 1);
   g_currentSpread = (Ask - Bid) / Point;
   
   // Calculate optimal lot
   double slPips = GetStopLoss(OP_BUY) / Point;
   if(slPips <= 0) slPips = InpDefaultSLPips;
   g_optimalLot = CalculateLot(slPips);
   
   // Update labels
   string balStr = "$" + DoubleToStr(g_accountBalance, 2);
   string eqStr = "$" + DoubleToStr(g_accountEquity, 2);
   string marginStr = "$" + DoubleToStr(AccountMargin(), 2);
   string freeMarginStr = "$" + DoubleToStr(AccountFreeMargin(), 2);
   
   double totalPL = 0;
   int totalTrades = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         totalPL += OrderProfit() + OrderSwap() + OrderCommission();
         totalTrades++;
      }
   }
   
   string dayPLStr = "$" + DoubleToStr(g_dailyProfitLoss, 2);
   if(g_dailyProfitLoss > 0) dayPLStr = "+" + dayPLStr;
   string totalPLStr = "$" + DoubleToStr(totalPL, 2);
   if(totalPL > 0) totalPLStr = "+" + totalPLStr;
   
   string riskStr = DoubleToStr(InpRiskPerTrade, 1) + "% ($" + 
                    DoubleToStr(g_accountBalance * InpRiskPerTrade / 100.0, 2) + ")";
   string lotStr = DoubleToStr(g_optimalLot, 2);
   string slStr = DoubleToStr(slPips, 0);
   
   double rr = GetRR(OP_BUY);
   string rrStr = "1:" + DoubleToStr(rr, 1);
   string tpStr = DoubleToStr(slPips * rr, 0);
   
   // Update text
   ObjectSetString(0, "DA_BAL", OBJPROP_TEXT, "Balance:   " + balStr);
   ObjectSetString(0, "DA_EQ", OBJPROP_TEXT, "Equity:    " + eqStr);
   ObjectSetString(0, "DA_MARG", OBJPROP_TEXT, "Margin:    " + marginStr);
   ObjectSetString(0, "DA_FMARG", OBJPROP_TEXT, "Free Mrg:  " + freeMarginStr);
   ObjectSetString(0, "DA_DAYPL", OBJPROP_TEXT, "Daily P/L: " + dayPLStr);
   ObjectSetString(0, "DA_TOTPL", OBJPROP_TEXT, "Total P/L: " + totalPLStr);
   ObjectSetString(0, "DA_RISK", OBJPROP_TEXT, "Risk:      " + riskStr);
   ObjectSetString(0, "DA_LOT", OBJPROP_TEXT, "Lot:       " + lotStr);
   ObjectSetString(0, "DA_SL", OBJPROP_TEXT, "SL:        " + slStr + " pips");
   ObjectSetString(0, "DA_RR", OBJPROP_TEXT, "RR:        " + rrStr);
   ObjectSetString(0, "DA_TP", OBJPROP_TEXT, "TP:        " + tpStr + " pips");
}

//+------------------------------------------------------------------+
//| Calculate optimal lot size based on risk per trade               |
//+------------------------------------------------------------------+
double CalculateLot(double slPips)
{
   if(InpUseFixedLot)
      return NormalizeDouble(InpFixedLotSize, 2);
   
   if(slPips <= 0) slPips = InpDefaultSLPips;
   
   double riskAmount = g_accountBalance * InpRiskPerTrade / 100.0;
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tickSize = MarketInfo(Symbol(), MODE_TICKSIZE);
   
   // If MT4 tick value is at 1 lot
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   double minLot = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
   
   if(tickValue > 0 && slPips > 0)
   {
      // Convert pips to ticks
      double ticksPerPip = 10; // Standard forex
      if(Digits() == 5 || Digits() == 3) ticksPerPip = 10;
      
      double slTicks = slPips * ticksPerPip;
      double lot = riskAmount / (slTicks * tickValue);
      
      // Round to lot step
      if(lotStep > 0)
         lot = MathFloor(lot / lotStep) * lotStep;
      
      if(lot < minLot) lot = minLot;
      if(lot > maxLot) lot = maxLot;
      
      return NormalizeDouble(lot, 2);
   }
   
   return NormalizeDouble(InpFixedLotSize, 2);
}

//+------------------------------------------------------------------+
//| Calculate stop loss in price                                    |
//+------------------------------------------------------------------+
double GetStopLoss(int tradeType)
{
   if(InpUseATRSL && g_currentATR > 0)
   {
      return g_currentATR * InpATRMultiplier;
   }
   
   return InpDefaultSLPips * Point * 10;
}

//+------------------------------------------------------------------+
//| Calculate Risk/Reward Ratio                                     |
//+------------------------------------------------------------------+
double GetRR(int tradeType)
{
   double slPips = GetStopLoss(tradeType) / (Point * 10);
   if(slPips <= 0) slPips = InpDefaultSLPips;
   
   // Default to 1:2 if no specific target
   double rr = InpMinRR;
   if(rr < 1.0) rr = 1.5;
   
   return rr;
}

//+------------------------------------------------------------------+
//| Place trade order                                                |
//+------------------------------------------------------------------+
void PlaceTrade(int tradeType)
{
   double slPips = GetStopLoss(tradeType) / Point;
   double rr = GetRR(tradeType);
   double lot = g_optimalLot;
   
   double price = (tradeType == OP_BUY) ? Ask : Bid;
   double sl = 0, tp = 0;
   
   if(tradeType == OP_BUY)
   {
      sl = price - slPips * Point;
      tp = price + (slPips * rr) * Point;
   }
   else
   {
      sl = price + slPips * Point;
      tp = price - (slPips * rr) * Point;
   }
   
   int digit = (int)MarketInfo(Symbol(), MODE_DIGITS);
   sl = NormalizeDouble(sl, digit);
   tp = NormalizeDouble(tp, digit);
   price = NormalizeDouble(price, digit);
   
   int ticket = OrderSend(Symbol(), tradeType, lot, price, 3,
                          sl, tp, 
                          "DA_Assistant", InpMagicNumber, 0,
                          (tradeType == OP_BUY) ? clrGreen : clrRed);
   
   if(ticket > 0 && InpShowAlerts)
   {
      string dirStr = (tradeType == OP_BUY) ? "BUY" : "SELL";
      string msg = "DA Assistant: " + dirStr + " " + DoubleToStr(lot, 2) + " lots @" + 
                   DoubleToStr(price, digit) + " | SL: " + DoubleToStr(sl, digit) + 
                   " | TP: " + DoubleToStr(tp, digit);
      
      Print(msg);
      Alert(msg);
   }
}

//+------------------------------------------------------------------+
//| Close all trades with magic number                               |
//+------------------------------------------------------------------+
void CloseAllTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber && InpMagicNumber != 0) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() <= OP_SELL)
      {
         double closePrice = (OrderType() == OP_BUY) ? Bid : Ask;
         if(!OrderClose(OrderTicket(), OrderLots(), closePrice, 3, clrWhite))
            Print("Failed to close #", OrderTicket());
      }
   }
}

//+------------------------------------------------------------------+
//| Close half of all positions                                      |
//+------------------------------------------------------------------+
void CloseHalfTrades()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderMagicNumber() != InpMagicNumber && InpMagicNumber != 0) continue;
      if(OrderSymbol() != Symbol()) continue;
      
      if(OrderType() <= OP_SELL)
      {
         double halfLots = NormalizeDouble(OrderLots() / 2.0, 2);
         double minLot = MarketInfo(Symbol(), MODE_MINLOT);
         
         if(halfLots >= minLot)
         {
            double closePrice = (OrderType() == OP_BUY) ? Bid : Ask;
            if(!OrderClose(OrderTicket(), halfLots, closePrice, 3, clrWhite))
               Print("Failed to close half of #", OrderTicket());
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate daily profit/loss                                      |
//+------------------------------------------------------------------+
void CalculateDailyPL()
{
   g_dailyProfitLoss = 0;
   
   // Check history for today
   MqlDateTime dt;
   TimeCurrent(dt);
   datetime todayStart = StringToTime(IntegerToString(dt.year) + "." + 
                                       IntegerToString(dt.mon) + "." + 
                                       IntegerToString(dt.day));
   
   for(int i = OrdersHistoryTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_HISTORY)) continue;
      if(OrderCloseTime() >= todayStart)
      {
         g_dailyProfitLoss += OrderProfit() + OrderSwap() + OrderCommission();
      }
   }
   
   // Add floating P/L from open trades
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      g_dailyProfitLoss += OrderProfit() + OrderSwap() + OrderCommission();
   }
}

//+------------------------------------------------------------------+
//| Helper function to create labels                                 |
//+------------------------------------------------------------------+
void CreateLabel(string name, int x, int y, string text, color clr, int fontSize, bool bold)
{
   ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
   ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_BACK, false);
   ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, name, OBJPROP_HIDDEN, true);
   
   if(bold)
   {
      ObjectSetString(0, name, OBJPROP_FONT, "Arial Bold");
   }
}
//+------------------------------------------------------------------+
