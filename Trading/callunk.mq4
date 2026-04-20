//+------------------------------------------------------------------+
//|                                                     callunk.mq4 |
//|         Currency Strength Dashboard + SMC Strategy EA           |
//|  Strategy: SMC (RSI + BOS + OB + FVG) + Currency Strength      |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, MetaQuotes Ltd."
#property link      "https://www.mql5.com"
#property version   "3.00"
#property strict

// ===== DISPLAY SETTINGS =====
input int    FontSize  = 9;
input color  TextColor = clrWhite;
input color  HeaderColor = clrYellow;
input int    StartX    = 10;
input int    StartY    = 30;
input int    LineHeight = 16;

// ===== CURRENCY PAIRS =====
input string CurrencyPairs = "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY";

// ===== TRADE SETTINGS =====
input double LotSize             = 0.01;
input int    MagicNumber         = 12345;
input int    MaxOpenPositions    = 3;
input double ATR_SL_Mult         = 1.5;
input double ATR_TP_Mult         = 3.0;
input int    Slippage            = 30;

// ===== INDICATOR SETTINGS =====
input int    SMA200_Period       = 200;
input int    RSI_Period          = 14;
input double RSI_OB              = 70.0;
input double RSI_OS              = 30.0;
input int    ATR_Period          = 14;

// ===== CURRENCY STRENGTH THRESHOLDS =====
input double StrongCurrencyThreshold = 7.0;
input double WeakCurrencyThreshold   = 2.0;

// ===== TRAILING STOP SETTINGS =====
input bool   EnableTrailingStop    = true;
input double TrailingStartProfit   = 1.0;
input double TrailingLockRatio     = 0.75;
input double TrailingStepSize      = 0.5;

// ===== SMC CONDITION TOGGLES =====
input string _COND_ = "=== SMC Condition Toggles ===";

// ===== SMC COLOR DEFINES =====
#define CLR_BULL      clrLime
#define CLR_BEAR      clrRed

// ===== SMC RUNTIME STATE =====
bool autoTradeON = false;
bool alertON     = true;   // toggle alert ON/OFF dari dashboard

// ===== DASHBOARD RUNTIME =====
string pairs[];
int totalPairs;
int RuntimeMaxOpenPositions;

// ===== TRAILING STOP TRACKING =====
struct TrailingStopData
{
   int ticket;
   double highestProfit;
   double currentLockLevel;
   bool isActive;
};
TrailingStopData trailingStops[];
int totalTrailingStops;

// ===== CURRENCY STRENGTH GLOBALS =====
string currencies[] = {"USD","EUR","GBP","CHF","CAD","AUD","JPY","NZD"};
int totalCurrencies = 8;
double ccy_strength[8];
int ccy_count[8];
string ccy_name[8];
string CurrencyPairs_CS = "GBPUSD,USDCHF,EURUSD,USDJPY,USDCAD,NZDUSD,AUDUSD,AUDNZD,AUDCAD,AUDCHF,AUDJPY,CADJPY,CHFJPY,EURGBP,EURAUD,EURCHF,EURJPY,EURNZD,EURCAD,GBPCHF,GBPAUD,GBPCAD,GBPJPY,GBPNZD,NZDJPY,NZDCAD,CHFCAD,NZDCHF";

datetime lastUpdateTime = 0;
int updateCounter = 0;
datetime lastClickTime = 0;
string lastClickedButton = "";

// ===== ALERT TRACKING =====
string lastAlertSignal[];   // "BUY", "SELL", or "" per pair
datetime lastAlertTime[];   // last alert time per pair

// Simple RGB helper
color RGB(int r, int g, int b) { return (color)((r & 0xFF) | ((g & 0xFF) << 8) | ((b & 0xFF) << 16)); }

//+------------------------------------------------------------------+
//| Active hours check                                               |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   RuntimeMaxOpenPositions = MaxOpenPositions;

   BuildPairsArray();
   InitializeTrailingStops();
   ArrayResize(lastAlertSignal, totalPairs);
   ArrayResize(lastAlertTime,   totalPairs);
   for(int ai=0; ai<totalPairs; ai++) { lastAlertSignal[ai]=""; lastAlertTime[ai]=0; }
   EventSetTimer(1);

   // Clean leftover session objects
   for(int oi = ObjectsTotal()-1; oi >= 0; oi--)
   {
      string n = ObjectName(oi);
      if(StringFind(n,"Time")>=0 || StringFind(n,"Waktu")>=0 ||
         StringFind(n,"Session")>=0 || StringFind(n,"TradingSession")>=0)
         ObjectDelete(0, n);
   }

   // Dashboard header
   CreateButton("HeaderPair",    "PAIR",      StartX,       StartY, 50, 18, clrGray, clrBlack);
   CreateLabel("HeaderProfit",   "PROFIT",    StartX+80,    StartY, HeaderColor, FontSize+2);
   int cx = StartX+150;
   CreateLabel("HeaderBuy",      "BUY",       cx+15,        StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderSell",     "SELL",      cx+65,        StartY, HeaderColor, FontSize+2);
   CreateButton("HeaderCloseAll","CLOSE ALL", cx+115,       StartY-2, 120, 18, clrGray, clrBlack);
   CreateLabel("HeaderCurrencySignal","CURR", cx+240,  StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderStrength", "STRENGTH",  cx+300,  StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderSMC_RSI",  "RSI",       cx+400,  StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderSMC_BOS",  "BOS",       cx+440,  StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderSMC_OB",   "OB",        cx+480,  StartY, HeaderColor, FontSize+2);
   CreateLabel("HeaderSMC_FVG",  "FVG",       cx+520,  StartY, HeaderColor, FontSize+2);

   CreateRowBackgrounds();

   for(int i = 0; i < totalPairs; i++)
   {
      int labelY = StartY + (i+2)*LineHeight - 8;
      int btnY   = StartY + (i+2)*LineHeight - 3;
      int btnH   = LineHeight - 1;
      CreateLabel("Pair_"+IntegerToString(i),   pairs[i],  StartX,    labelY, TextColor, FontSize);
      CreateLabel("Spread_"+IntegerToString(i), "Loading...", StartX+80, labelY, TextColor, FontSize);
      CreateButton("BuyButton_"+IntegerToString(i),   "BUY",    cx+15,  btnY, 40, btnH, clrDarkGreen, clrWhite);
      CreateButton("SellButton_"+IntegerToString(i),  "SELL",   cx+65,  btnY, 40, btnH, clrDarkRed,   clrWhite);
      CreateButton("CloseButton_"+IntegerToString(i), "NO POS", cx+115, btnY, 120, btnH, clrGray, clrBlack);
      CreateLabel("CurrencySignal_"+IntegerToString(i), "WAIT", cx+240, labelY, TextColor, FontSize);
      CreateLabel("SMC_RSI_"+IntegerToString(i), "-", cx+400, labelY, clrGray, FontSize);
      CreateLabel("SMC_BOS_"+IntegerToString(i), "-", cx+440, labelY, clrGray, FontSize);
      CreateLabel("SMC_OB_" +IntegerToString(i), "-", cx+480, labelY, clrGray, FontSize);
      CreateLabel("SMC_FVG_"+IntegerToString(i), "-", cx+520, labelY, clrGray, FontSize);
   }

   CreateMaxOrderInput();

   UpdateProfits();
   ChartRedraw();
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();

   ObjectDelete(0,"HeaderPair"); ObjectDelete(0,"HeaderProfit");
   ObjectDelete(0,"HeaderBuy");  ObjectDelete(0,"HeaderSell");
   ObjectDelete(0,"HeaderCurrencySignal");
   ObjectDelete(0,"HeaderStrength"); ObjectDelete(0,"HeaderCloseAll");
   ObjectDelete(0,"HeaderSMC_RSI"); ObjectDelete(0,"HeaderSMC_BOS");
   ObjectDelete(0,"HeaderSMC_OB");  ObjectDelete(0,"HeaderSMC_FVG");

   for(int i=0; i<totalPairs; i++)
   {
      ObjectDelete(0,"RowBG_"+IntegerToString(i));
      ObjectDelete(0,"Pair_"+IntegerToString(i));
      ObjectDelete(0,"Spread_"+IntegerToString(i));
      ObjectDelete(0,"BuyButton_"+IntegerToString(i));
      ObjectDelete(0,"SellButton_"+IntegerToString(i));
      ObjectDelete(0,"CloseButton_"+IntegerToString(i));
      ObjectDelete(0,"CurrencySignal_"+IntegerToString(i));
      ObjectDelete(0,"SMC_RSI_"+IntegerToString(i));
      ObjectDelete(0,"SMC_BOS_"+IntegerToString(i));
      ObjectDelete(0,"SMC_OB_" +IntegerToString(i));
      ObjectDelete(0,"SMC_FVG_"+IntegerToString(i));
   }
   for(int c=0; c<totalCurrencies; c++) ObjectDelete(0,"Strength_"+IntegerToString(c));

   ObjectDelete(0,"MaxOrderLabel"); ObjectDelete(0,"MaxOrderMinus");
   ObjectDelete(0,"MaxOrderValue"); ObjectDelete(0,"MaxOrderPlus");
   ObjectDelete(0,"SaldoLabel");    ObjectDelete(0,"SaldoValue");
   ObjectDelete(0,"MarginLabel");   ObjectDelete(0,"MarginValue");
   ObjectDelete(0,"BtnAutoTrade");
   ObjectDelete(0,"BtnAlert");

   for(int oi=ObjectsTotal()-1; oi>=0; oi--)
   {
      string n = ObjectName(oi);
      if(StringFind(n,"Time")>=0 || StringFind(n,"Waktu")>=0 ||
         StringFind(n,"Session")>=0 || StringFind(n,"TradingSession")>=0)
         ObjectDelete(0, n);
   }
}

//+------------------------------------------------------------------+
//| OnTick                                                           |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime currentTime = TimeCurrent();
   if(currentTime == lastUpdateTime) return;

   UpdateProfits();
   UpdateCloseButtons();
   UpdatePairColors();
   UpdateProfitHeaderColor();
   UpdateCloseAllButton();

   if(EnableTrailingStop) ManageTrailingStops();

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| OnTimer                                                          |
//+------------------------------------------------------------------+
void OnTimer()
{
   datetime currentTime = TimeCurrent();
   if(currentTime == lastUpdateTime) return;
   lastUpdateTime = currentTime;
   updateCounter++;

   UpdateProfits();
   UpdateCloseButtons();
   UpdatePairColors();
   UpdateProfitHeaderColor();
   UpdateCloseAllButton();
   UpdateMaxOrderDisplay();

   if(updateCounter % 2 == 0)
   {
      UpdateCurrencySignals();
      UpdateSMCSignals();
      CheckAlertSignals();
      if(autoTradeON) RunAutoTrade();
   }
   if(updateCounter % 5 == 0) UpdateCurrencyStrength();

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| OnChartEvent                                                     |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id != CHARTEVENT_OBJECT_CLICK) return;

   // Anti-double-click
   datetime currentTime = TimeCurrent();
   if(lastClickedButton == sparam && (currentTime - lastClickTime) < 1)
   {
      ObjectSetInteger(0, sparam, OBJPROP_SELECTED, false);
      return;
   }
   lastClickTime = currentTime;
   lastClickedButton = sparam;

   // ---- Dashboard buttons ----
   if(StringFind(sparam,"BuyButton_") == 0)
   {
      int idx = (int)StringToInteger(StringSubstr(sparam,10));
      if(idx >= 0 && idx < totalPairs) OpenTrade(pairs[idx], OP_BUY);
      ObjectSetInteger(0, sparam, OBJPROP_SELECTED, false); return;
   }
   if(StringFind(sparam,"SellButton_") == 0)
   {
      int idx = (int)StringToInteger(StringSubstr(sparam,11));
      if(idx >= 0 && idx < totalPairs) OpenTrade(pairs[idx], OP_SELL);
      ObjectSetInteger(0, sparam, OBJPROP_SELECTED, false); return;
   }
   if(StringFind(sparam,"CloseButton_") == 0)
   {
      int idx = (int)StringToInteger(StringSubstr(sparam,12));
      if(idx >= 0 && idx < totalPairs)
      {
         bool hasPOS = false;
         for(int j=0; j<OrdersTotal(); j++)
            if(OrderSelect(j,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==pairs[idx] && OrderMagicNumber()==MagicNumber)
               { hasPOS=true; break; }
         if(hasPOS) ClosePositions(pairs[idx]);
      }
      ObjectSetInteger(0, sparam, OBJPROP_SELECTED, false); return;
   }
   if(StringFind(sparam,"HeaderPair") == 0)   { ObjectSetInteger(0,"HeaderPair",OBJPROP_SELECTED,false); return; }
   if(StringFind(sparam,"HeaderCloseAll") == 0){ CloseAllPositions(); ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_SELECTED,false); return; }
   if(StringFind(sparam,"RowBG_") == 0)        { return; }
   if(StringFind(sparam,"MaxOrderMinus") == 0)
   {
      if(RuntimeMaxOpenPositions > 1) { RuntimeMaxOpenPositions--; UpdateMaxOrderDisplay(); }
      ObjectSetInteger(0,"MaxOrderMinus",OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"MaxOrderPlus") == 0)
   {
      if(RuntimeMaxOpenPositions < 10) { RuntimeMaxOpenPositions++; UpdateMaxOrderDisplay(); }
      ObjectSetInteger(0,"MaxOrderPlus",OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"BtnAutoTrade") == 0)
   {
      autoTradeON = !autoTradeON;
      UpdateAutoTradeButton();
      ObjectSetInteger(0,"BtnAutoTrade",OBJPROP_SELECTED,false); return;
   }
   if(StringFind(sparam,"BtnAlert") == 0)
   {
      alertON = !alertON;
      UpdateAlertButton();
      ObjectSetInteger(0,"BtnAlert",OBJPROP_SELECTED,false); return;
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Create label                                          |
//+------------------------------------------------------------------+
void CreateLabel(string name, string text, int x, int y, color clr, int fontSize)
{
   ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetString(0,  name, OBJPROP_TEXT,      text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,     clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,  fontSize);
   ObjectSetString(0,  name, OBJPROP_FONT,      "Segoe UI");
   ObjectSetInteger(0, name, OBJPROP_CORNER,    CORNER_LEFT_UPPER);
   ObjectSetInteger(0, name, OBJPROP_ANCHOR,    ANCHOR_LEFT_UPPER);
}

//+------------------------------------------------------------------+
//| Dashboard: Create button                                         |
//+------------------------------------------------------------------+
void CreateButton(string name, string text, int x, int y, int width, int height, color bgColor, color textColor)
{
   if(ObjectFind(0, name) < 0)
   {
      ObjectCreate(0, name, OBJ_BUTTON, 0, 0, 0);
      ObjectSetInteger(0, name, OBJPROP_CORNER,     CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK,       false);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, true);
      ObjectSetInteger(0, name, OBJPROP_SELECTED,   false);
   }
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE,   x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE,   y);
   ObjectSetInteger(0, name, OBJPROP_XSIZE,       width);
   ObjectSetInteger(0, name, OBJPROP_YSIZE,       height);
   ObjectSetString(0,  name, OBJPROP_TEXT,        text);
   ObjectSetInteger(0, name, OBJPROP_COLOR,       textColor);
   ObjectSetInteger(0, name, OBJPROP_BGCOLOR,     bgColor);
   ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR,clrGray);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE,    FontSize);
   ObjectSetString(0,  name, OBJPROP_FONT,        "Segoe UI");
}

//+------------------------------------------------------------------+
//| Dashboard: Create max order input                                |
//+------------------------------------------------------------------+
void CreateMaxOrderInput()
{
   int inputY = StartY + (totalPairs+3)*LineHeight;
   CreateLabel("MaxOrderLabel", "MAX ORDER:", StartX, inputY, HeaderColor, FontSize);
   CreateButton("MaxOrderMinus", "-", StartX+90,  inputY-2, 20, 15, clrRed,  clrWhite);
   CreateLabel("MaxOrderValue",  IntegerToString(RuntimeMaxOpenPositions), StartX+125, inputY, clrLime, FontSize+1);
   CreateButton("MaxOrderPlus",  "+", StartX+150, inputY-2, 20, 15, clrLime, clrBlack);

   int infoY = inputY + LineHeight;
   CreateLabel("SaldoLabel",  "SALDO:",       StartX,     infoY, HeaderColor, FontSize-2);
   CreateLabel("SaldoValue",  "$"+DoubleToString(AccountBalance(),2), StartX+50, infoY, clrLime, FontSize-2);
   CreateLabel("MarginLabel", "MARGIN SISA:", StartX+150, infoY, HeaderColor, FontSize-2);
   CreateLabel("MarginValue", "$"+DoubleToString(AccountFreeMargin(),2), StartX+230, infoY, clrLime, FontSize-2);
   CreateButton("BtnAutoTrade", "AUTO: OFF", StartX+350, infoY-2, 100, 16, C'50,50,50', clrGray);
   CreateButton("BtnAlert",     "ALERT: ON", StartX+460, infoY-2, 100, 16, C'0,100,0',  clrLime);
}

//+------------------------------------------------------------------+
//| Dashboard: Update max order display                              |
//+------------------------------------------------------------------+
void UpdateMaxOrderDisplay()
{
   ObjectSetString(0,"MaxOrderValue", OBJPROP_TEXT, IntegerToString(RuntimeMaxOpenPositions));
   ObjectSetString(0,"SaldoValue",    OBJPROP_TEXT, "$"+DoubleToString(AccountBalance(),2));
   ObjectSetString(0,"MarginValue",   OBJPROP_TEXT, "$"+DoubleToString(AccountFreeMargin(),2));
}

//+------------------------------------------------------------------+
//| Dashboard: Create row separators (thin horizontal lines)        |
//+------------------------------------------------------------------+
void CreateRowBackgrounds()
{
   int lineWidth = 150 + 820;
   for(int i=0; i<totalPairs; i++)
   {
      string bgName = "RowBG_"+IntegerToString(i);
      int lineY = StartY + (i+2)*LineHeight + LineHeight - 5;
      ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE,    StartX-2);
      ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE,    lineY);
      ObjectSetInteger(0, bgName, OBJPROP_XSIZE,        lineWidth);
      ObjectSetInteger(0, bgName, OBJPROP_YSIZE,        1);
      ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR,      RGB(70,70,70));
      ObjectSetInteger(0, bgName, OBJPROP_BORDER_COLOR, RGB(70,70,70));
      ObjectSetInteger(0, bgName, OBJPROP_CORNER,       CORNER_LEFT_UPPER);
      ObjectSetInteger(0, bgName, OBJPROP_STYLE,        STYLE_SOLID);
      ObjectSetInteger(0, bgName, OBJPROP_BACK,         true);
      ObjectSetInteger(0, bgName, OBJPROP_SELECTABLE,   false);
      ObjectSetInteger(0, bgName, OBJPROP_SELECTED,     false);
      ObjectSetInteger(0, bgName, OBJPROP_HIDDEN,       false);
      ObjectSetInteger(0, bgName, OBJPROP_ZORDER,       0);
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update profits                                        |
//+------------------------------------------------------------------+
void UpdateProfits()
{
   for(int i=0; i<totalPairs; i++)
   {
      string symbol = pairs[i];
      double totalProfit = 0.0;
      int orderCount = 0;
      for(int j=0; j<OrdersTotal(); j++)
         if(OrderSelect(j,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==symbol && OrderMagicNumber()==MagicNumber)
            { totalProfit += OrderProfit()+OrderSwap()+OrderCommission(); orderCount++; }

      string profitText; color profitColor;
      if(orderCount > 0)
      {
         if(totalProfit > 0)      { profitText="+"+DoubleToString(totalProfit,2); profitColor=clrLime; }
         else if(totalProfit < 0) { profitText=DoubleToString(totalProfit,2);     profitColor=clrRed;  }
         else                     { profitText="0.00";                            profitColor=TextColor; }
      }
      else { profitText="No Trades"; profitColor=clrGray; }

      ObjectSetString(0,  "Spread_"+IntegerToString(i), OBJPROP_TEXT,  profitText);
      ObjectSetInteger(0, "Spread_"+IntegerToString(i), OBJPROP_COLOR, profitColor);
   }
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Dashboard: Update close buttons                                  |
//+------------------------------------------------------------------+
void UpdateCloseButtons()
{
   for(int i=0; i<totalPairs; i++)
   {
      string symbol = pairs[i];
      bool hasBuy=false, hasSell=false;
      int posCount=0;
      double totalProfit=0.0;
      for(int j=0; j<OrdersTotal(); j++)
         if(OrderSelect(j,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==symbol && OrderMagicNumber()==MagicNumber)
         {
            if(OrderType()==OP_BUY)  hasBuy=true;
            if(OrderType()==OP_SELL) hasSell=true;
            totalProfit += OrderProfit()+OrderSwap()+OrderCommission();
            posCount++;
         }

      string btnText="NO POS"; color btnBg=clrGray, btnTxt=clrBlack;
      if(posCount > 0)
      {
         if(hasBuy && hasSell) btnText="CLOSE ALL";
         else if(hasBuy)       btnText="CLOSE BUY";
         else                  btnText="CLOSE SELL";
         if(totalProfit > 0)      { btnBg=clrLime;   btnTxt=clrBlack; }
         else if(totalProfit < 0) { btnBg=clrRed;    btnTxt=clrWhite; }
         else                     { btnBg=clrYellow; btnTxt=clrBlack; }
      }
      ObjectSetInteger(0,"CloseButton_"+IntegerToString(i), OBJPROP_BGCOLOR, btnBg);
      ObjectSetString(0, "CloseButton_"+IntegerToString(i), OBJPROP_TEXT,    btnText);
      ObjectSetInteger(0,"CloseButton_"+IntegerToString(i), OBJPROP_COLOR,   btnTxt);
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update pair colors                                    |
//+------------------------------------------------------------------+
void UpdatePairColors()
{
   for(int i=0; i<totalPairs; i++)
   {
      string symbol = pairs[i];
      double totalProfit=0.0; int orderCount=0;
      for(int j=0; j<OrdersTotal(); j++)
         if(OrderSelect(j,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==symbol && OrderMagicNumber()==MagicNumber)
            { totalProfit += OrderProfit()+OrderSwap()+OrderCommission(); orderCount++; }

      color pairColor = TextColor;
      if(orderCount > 0)
      {
         if(totalProfit > 0)      pairColor = clrLime;
         else if(totalProfit < 0) pairColor = clrRed;
      }
      ObjectSetInteger(0,"Pair_"+IntegerToString(i), OBJPROP_COLOR, pairColor);
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update profit header color                            |
//+------------------------------------------------------------------+
void UpdateProfitHeaderColor()
{
   double totalAllProfit=0.0; int totalOrderCount=0;
   for(int i=0; i<OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderMagicNumber()==MagicNumber)
         { totalAllProfit += OrderProfit()+OrderSwap()+OrderCommission(); totalOrderCount++; }

   color hdrColor = HeaderColor;
   if(totalOrderCount > 0)
   {
      if(totalAllProfit > 0)      hdrColor = clrLime;
      else if(totalAllProfit < 0) hdrColor = clrRed;
   }
   ObjectSetInteger(0,"HeaderProfit", OBJPROP_COLOR, hdrColor);
}

//+------------------------------------------------------------------+
//| Dashboard: Update CLOSE ALL button                               |
//+------------------------------------------------------------------+
void UpdateCloseAllButton()
{
   double totalAllProfit=0.0; int totalOrderCount=0;
   for(int i=0; i<OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderMagicNumber()==MagicNumber)
         { totalAllProfit += OrderProfit()+OrderSwap()+OrderCommission(); totalOrderCount++; }

   color btnColor=clrGray, txtColor=clrBlack;
   string btnText="CLOSE ALL";
   if(totalOrderCount > 0)
   {
      string profitStr = (totalAllProfit>=0) ? "+"+DoubleToString(totalAllProfit,2) : DoubleToString(totalAllProfit,2);
      btnText = "CLOSE ALL "+profitStr;
      if(totalAllProfit > 0)      { btnColor=clrLime;   txtColor=clrBlack; }
      else if(totalAllProfit < 0) { btnColor=clrRed;    txtColor=clrWhite; }
      else                        { btnColor=clrYellow; txtColor=clrBlack; }
   }
   btnText = btnText+" ("+IntegerToString(totalOrderCount)+"/"+IntegerToString(RuntimeMaxOpenPositions)+")";
   ObjectSetInteger(0,"HeaderCloseAll", OBJPROP_BGCOLOR, btnColor);
   ObjectSetString(0, "HeaderCloseAll", OBJPROP_TEXT,    btnText);
   ObjectSetInteger(0,"HeaderCloseAll", OBJPROP_COLOR,   txtColor);
}

//+------------------------------------------------------------------+
//| Dashboard: Close positions for symbol                           |
//+------------------------------------------------------------------+
void ClosePositions(string symbol)
{
   int closedCount=0;
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderSymbol()!=symbol || OrderMagicNumber()!=MagicNumber) continue;
      double closePrice; color arrowColor;
      if(OrderType()==OP_BUY)       { closePrice=SymbolInfoDouble(symbol,SYMBOL_BID); arrowColor=clrRed;  }
      else if(OrderType()==OP_SELL) { closePrice=SymbolInfoDouble(symbol,SYMBOL_ASK); arrowColor=clrBlue; }
      else continue;
      if(OrderClose(OrderTicket(), OrderLots(), closePrice, 3, arrowColor)) closedCount++;
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Close all positions                                   |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber) continue;
      double closePrice; color arrowColor;
      if(OrderType()==OP_BUY)       { closePrice=SymbolInfoDouble(OrderSymbol(),SYMBOL_BID); arrowColor=clrRed;  }
      else if(OrderType()==OP_SELL) { closePrice=SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK); arrowColor=clrBlue; }
      else continue;
      if(!OrderClose(OrderTicket(), OrderLots(), closePrice, 3, arrowColor))
         Print("OrderClose error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update currency signals                               |
//+------------------------------------------------------------------+
void UpdateCurrencySignals()
{
   double strength[8];
   CalculateCurrencyStrength(strength);
   for(int i=0; i<totalPairs; i++)
   {
      string symbol = pairs[i];
      string sig = AnalyzeCurrencyStrengthSignal(symbol, strength);
      ObjectSetString(0,  "CurrencySignal_"+IntegerToString(i), OBJPROP_TEXT,  sig);
      color sigColor = (sig=="BUY") ? clrLime : (sig=="SELL") ? clrRed : clrGray;
      ObjectSetInteger(0, "CurrencySignal_"+IntegerToString(i), OBJPROP_COLOR, sigColor);
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update SMC signals per pair                           |
//+------------------------------------------------------------------+
void UpdateSMCSignals()
{
   for(int i=0; i<totalPairs; i++)
   {
      string sym = pairs[i];

      // RSI
      double rsi   = iRSI(sym, 0, RSI_Period, PRICE_CLOSE, 1);
      bool rsiBull = (rsi > 50 && rsi < RSI_OB);
      bool rsiBear = (rsi < 50 && rsi > RSI_OS);

      // BOS
      double c1 = iClose(sym,0,1), c2 = iClose(sym,0,2);
      double prevHH = 0, prevLL = 999999;
      for(int b=3; b<13; b++) { if(iHigh(sym,0,b)>prevHH) prevHH=iHigh(sym,0,b); if(iLow(sym,0,b)<prevLL) prevLL=iLow(sym,0,b); }
      bool bosBull = (c1 > prevHH && c2 <= prevHH);
      bool bosBear = (c1 < prevLL && c2 >= prevLL);

      // OB
      double o2 = iOpen(sym,0,2);
      bool obBull = (c2 < o2) && (c1 > o2);
      bool obBear = (c2 > o2) && (c1 < o2);

      // FVG
      bool fvgBull = (iLow(sym,0,1)  > iHigh(sym,0,3));
      bool fvgBear = (iHigh(sym,0,1) < iLow(sym,0,3));

      // Helper: set each label text + color
      SetSMCLabel("SMC_RSI_"+IntegerToString(i), rsiBull, rsiBear);
      SetSMCLabel("SMC_BOS_"+IntegerToString(i), bosBull, bosBear);
      SetSMCLabel("SMC_OB_" +IntegerToString(i), obBull,  obBear);
      SetSMCLabel("SMC_FVG_"+IntegerToString(i), fvgBull, fvgBear);
   }
}

void SetSMCLabel(string name, bool isBull, bool isBear)
{
   string txt  = isBull ? "BUY"  : (isBear ? "SELL" : "-");
   color  clr  = isBull ? clrLime : (isBear ? clrRed : clrGray);
   ObjectSetString(0,  name, OBJPROP_TEXT,  txt);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| Count how many of 5 signals agree (CURR+RSI+BOS+OB+FVG)        |
//+------------------------------------------------------------------+
int CountSMCSignals(string sym, double &strength[], bool &isBuy)
{
   // CURR
   string currSig = AnalyzeCurrencyStrengthSignal(sym, strength);
   bool currBull  = (currSig == "BUY");
   bool currBear  = (currSig == "SELL");

   // RSI
   double rsi   = iRSI(sym, 0, RSI_Period, PRICE_CLOSE, 1);
   bool rsiBull = (rsi > 50 && rsi < RSI_OB);
   bool rsiBear = (rsi < 50 && rsi > RSI_OS);

   // BOS
   double c1 = iClose(sym,0,1), c2 = iClose(sym,0,2);
   double prevHH = 0, prevLL = 999999;
   for(int b=3; b<13; b++) { if(iHigh(sym,0,b)>prevHH) prevHH=iHigh(sym,0,b); if(iLow(sym,0,b)<prevLL) prevLL=iLow(sym,0,b); }
   bool bosBull = (c1 > prevHH && c2 <= prevHH);
   bool bosBear = (c1 < prevLL && c2 >= prevLL);

   // OB
   double o2 = iOpen(sym,0,2);
   bool obBull = (c2 < o2) && (c1 > o2);
   bool obBear = (c2 > o2) && (c1 < o2);

   // FVG
   bool fvgBull = (iLow(sym,0,1)  > iHigh(sym,0,3));
   bool fvgBear = (iHigh(sym,0,1) < iLow(sym,0,3));

   int bulls = (currBull?1:0)+(rsiBull?1:0)+(bosBull?1:0)+(obBull?1:0)+(fvgBull?1:0);
   int bears = (currBear?1:0)+(rsiBear?1:0)+(bosBear?1:0)+(obBear?1:0)+(fvgBear?1:0);

   if(bulls >= bears) { isBuy = true;  return bulls; }
   else               { isBuy = false; return bears; }
}

//+------------------------------------------------------------------+
//| Check all pairs for alert condition (>=4 of 5 signals)          |
//+------------------------------------------------------------------+
void CheckAlertSignals()
{
   double strength[8];
   CalculateCurrencyStrength(strength);

   for(int i=0; i<totalPairs; i++)
   {
      string sym = pairs[i];
      bool   isBuy;
      int    score = CountSMCSignals(sym, strength, isBuy);
      if(score < 4) { lastAlertSignal[i] = ""; continue; }

      string dir = isBuy ? "BUY" : "SELL";

      // Skip if open position already exists in same direction
      int opType = isBuy ? OP_BUY : OP_SELL;
      if(HasOpenPosition(sym, opType)) { lastAlertSignal[i] = ""; continue; }

      // Skip if same signal already alerted within last 5 minutes
      if(lastAlertSignal[i] == dir && (TimeCurrent()-lastAlertTime[i]) < 300) continue;

      lastAlertSignal[i] = dir;
      lastAlertTime[i]   = TimeCurrent();

      string msg = "SIGNAL "+dir+" | "+sym+" | "+IntegerToString(score)+"/5 signals";
      if(alertON)
      {
         Alert(msg);
         SendNotification(msg);
      }
      Print(msg);
   }
}

//+------------------------------------------------------------------+
//| Auto trade button display                                        |
//+------------------------------------------------------------------+
void UpdateAutoTradeButton()
{
   string txt  = autoTradeON ? "AUTO: ON"  : "AUTO: OFF";
   color  bg   = autoTradeON ? clrDarkGreen : C'50,50,50';
   color  clr  = autoTradeON ? clrLime      : clrGray;
   ObjectSetString(0,  "BtnAutoTrade", OBJPROP_TEXT,    txt);
   ObjectSetInteger(0, "BtnAutoTrade", OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, "BtnAutoTrade", OBJPROP_COLOR,   clr);
}

//+------------------------------------------------------------------+
//| Alert button display                                             |
//+------------------------------------------------------------------+
void UpdateAlertButton()
{
   string txt = alertON ? "ALERT: ON"  : "ALERT: OFF";
   color  bg  = alertON ? C'0,100,0'   : C'50,50,50';
   color  clr = alertON ? clrLime       : clrGray;
   ObjectSetString(0,  "BtnAlert", OBJPROP_TEXT,    txt);
   ObjectSetInteger(0, "BtnAlert", OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, "BtnAlert", OBJPROP_COLOR,   clr);
}

//+------------------------------------------------------------------+
//| Auto trade: open/close per pair based on >=4 signals            |
//+------------------------------------------------------------------+
void RunAutoTrade()
{
   double strength[8];
   CalculateCurrencyStrength(strength);

   for(int i=0; i<totalPairs; i++)
   {
      string sym     = pairs[i];
      bool   isBuy;
      int    score   = CountSMCSignals(sym, strength, isBuy);
      if(score < 4) continue;

      int dirType = isBuy ? OP_BUY  : OP_SELL;
      int oppType = isBuy ? OP_SELL : OP_BUY;

      // Close opposite direction first, then recount
      if(HasOpenPosition(sym, oppType)) { ClosePositions(sym); Sleep(300); }

      // Already open in same direction — nothing to do
      if(HasOpenPosition(sym, dirType)) continue;

      // Respect max open positions AFTER any close above
      if(CountOpenPositions() >= RuntimeMaxOpenPositions) continue;

      OpenTrade(sym, dirType);
   }
}

//+------------------------------------------------------------------+
//| Dashboard: Update currency strength display                      |
//+------------------------------------------------------------------+
void UpdateCurrencyStrength()
{
   double strength[8];
   CalculateCurrencyStrength(strength);
   int sortedIndex[8];
   SortCurrenciesByStrength(strength, sortedIndex);
   int cx = StartX + 150;
   for(int i=0; i<totalCurrencies; i++)
   {
      int ci = sortedIndex[i];
      string lbl = "Strength_"+IntegerToString(i);
      string txt = IntegerToString(i+1)+" "+currencies[ci]+" "+DoubleToString(strength[ci],1);
      if(ObjectFind(0,lbl) < 0) ObjectCreate(0, lbl, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, lbl, OBJPROP_XDISTANCE, cx+300);
      ObjectSetInteger(0, lbl, OBJPROP_YDISTANCE, StartY+(i+2)*LineHeight+2);
      ObjectSetString(0,  lbl, OBJPROP_TEXT,      txt);
      ObjectSetInteger(0, lbl, OBJPROP_FONTSIZE,  FontSize);
      ObjectSetString(0,  lbl, OBJPROP_FONT,      "Segoe UI");
      color tc = (strength[ci]>=StrongCurrencyThreshold) ? clrLime : (strength[ci]<=WeakCurrencyThreshold) ? clrRed : clrWhite;
      ObjectSetInteger(0, lbl, OBJPROP_COLOR, tc);
   }
}

//+------------------------------------------------------------------+
//| Position helpers                                                 |
//+------------------------------------------------------------------+
bool HasOpenPosition(string symbol, int orderType)
{
   for(int i=0; i<OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==symbol &&
         OrderMagicNumber()==MagicNumber && OrderType()==orderType) return true;
   return false;
}
bool HasAnyOpenPosition(string symbol)
{
   for(int i=0; i<OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==symbol &&
         OrderMagicNumber()==MagicNumber && (OrderType()==OP_BUY||OrderType()==OP_SELL)) return true;
   return false;
}
int CountOpenPositions()
{
   int count=0;
   for(int i=0; i<OrdersTotal(); i++)
      if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderMagicNumber()==MagicNumber &&
         (OrderType()==OP_BUY||OrderType()==OP_SELL)) count++;
   return count;
}

//+------------------------------------------------------------------+
//| Currency Strength calculation (Giraia logic)                    |
//+------------------------------------------------------------------+
void CalculateCurrencyStrength(double &strength[])
{
   ArrayInitialize(ccy_strength, 0.0);
   ArrayInitialize(ccy_count, 0);
   ccy_name[0]="USD"; ccy_name[1]="EUR"; ccy_name[2]="GBP"; ccy_name[3]="CHF";
   ccy_name[4]="CAD"; ccy_name[5]="AUD"; ccy_name[6]="JPY"; ccy_name[7]="NZD";

   string pairsArray[];
   int pairCount = StringSplit(CurrencyPairs_CS, ',', pairsArray);
   for(int i=0; i<pairCount; i++)
   {
      string pair = pairsArray[i];
      double day_high = MarketInfo(pair,MODE_HIGH);
      double day_low  = MarketInfo(pair,MODE_LOW);
      double curr_bid = MarketInfo(pair,MODE_BID);
      if(day_high>0 && day_low>0 && curr_bid>0)
      {
         double bid_ratio = DivZero(curr_bid-day_low, day_high-day_low);
         double ind_strength = 0;
         if(bid_ratio>=0.97)      ind_strength=9;
         else if(bid_ratio>=0.90) ind_strength=8;
         else if(bid_ratio>=0.75) ind_strength=7;
         else if(bid_ratio>=0.60) ind_strength=6;
         else if(bid_ratio>=0.50) ind_strength=5;
         else if(bid_ratio>=0.40) ind_strength=4;
         else if(bid_ratio>=0.25) ind_strength=3;
         else if(bid_ratio>=0.10) ind_strength=2;
         else if(bid_ratio>=0.03) ind_strength=1;

         string base  = StringSubstr(pair,0,3);
         string quote = StringSubstr(pair,3,3);
         for(int j=0; j<8; j++) if(ccy_name[j]==base)  { ccy_strength[j]+=ind_strength;   ccy_count[j]++; break; }
         for(int k=0; k<8; k++) if(ccy_name[k]==quote) { ccy_strength[k]+=9-ind_strength; ccy_count[k]++; break; }
      }
   }
   for(int c=0; c<8; c++)
      strength[c] = (ccy_count[c]>0) ? DivZero(ccy_strength[c],ccy_count[c]) : 5.0;
}

double DivZero(double n, double d) { return (d==0) ? 0 : 1.0*n/d; }

int GetCurrencyIndex(string code)
{
   for(int i=0; i<totalCurrencies; i++) if(currencies[i]==code) return i;
   return -1;
}

void SortCurrenciesByStrength(double &strength[], int &sortedIndex[])
{
   for(int i=0; i<totalCurrencies; i++) sortedIndex[i]=i;
   for(int i=0; i<totalCurrencies-1; i++)
      for(int j=0; j<totalCurrencies-1-i; j++)
         if(strength[sortedIndex[j]] < strength[sortedIndex[j+1]])
            { int tmp=sortedIndex[j]; sortedIndex[j]=sortedIndex[j+1]; sortedIndex[j+1]=tmp; }
}

string AnalyzeCurrencyStrengthSignal(string symbol, double &strength[])
{
   int bi = GetCurrencyIndex(StringSubstr(symbol,0,3));
   int qi = GetCurrencyIndex(StringSubstr(symbol,3,3));
   if(bi<0 || qi<0) return "WAIT";
   double bs=strength[bi], qs=strength[qi];
   if(bs>=StrongCurrencyThreshold && qs<=WeakCurrencyThreshold) return "BUY";
   if(qs>=StrongCurrencyThreshold && bs<=WeakCurrencyThreshold) return "SELL";
   return "WAIT";
}

//+------------------------------------------------------------------+
//| Build pairs array                                                |
//+------------------------------------------------------------------+
void BuildPairsArray()
{
   string pairString = CurrencyPairs;
   StringReplace(pairString," ","");
   totalPairs=1;
   for(int i=0; i<StringLen(pairString); i++)
      if(StringGetCharacter(pairString,i)==',') totalPairs++;
   if(StringLen(pairString)==0) { totalPairs=0; return; }
   ArrayResize(pairs, totalPairs);
   int start=0, pairIndex=0;
   for(int i=0; i<=StringLen(pairString); i++)
   {
      if(i==StringLen(pairString) || StringGetCharacter(pairString,i)==',')
      {
         if(i>start) { string p=StringSubstr(pairString,start,i-start); if(StringLen(p)>0) pairs[pairIndex++]=p; }
         start=i+1;
      }
   }
   totalPairs=pairIndex;
   ArrayResize(pairs, totalPairs);
}

//+------------------------------------------------------------------+
//| Open trade (currency dashboard)                                  |
//+------------------------------------------------------------------+
void OpenTrade(string symbol, int orderType)
{
   if(!IsTradeAllowed()) { Print("Trading not allowed"); return; }
   if(!SymbolSelect(symbol,true)) { Print("Symbol not available: ",symbol); return; }

   double ask = SymbolInfoDouble(symbol,SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol,SYMBOL_BID);
   if(ask<=0 || bid<=0) { Print("Invalid prices for ",symbol); return; }

   double lotSize = NormalizeDouble(LotSize,2);
   double minLot  = SymbolInfoDouble(symbol,SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(symbol,SYMBOL_VOLUME_MAX);
   if(lotSize<minLot) lotSize=minLot;
   if(lotSize>maxLot) lotSize=maxLot;

   double requiredMargin = MarketInfo(symbol,MODE_MARGINREQUIRED)*lotSize;
   if(requiredMargin > AccountFreeMargin()) { Print("Insufficient margin for ",symbol); return; }

   int    digs  = (int)MarketInfo(symbol, MODE_DIGITS);
   double atr   = iATR(symbol, 0, ATR_Period, 1);
   double price = (orderType==OP_BUY) ? ask : bid;
   double sl    = (orderType==OP_BUY) ? price - atr*ATR_SL_Mult : price + atr*ATR_SL_Mult;
   double tp    = (orderType==OP_BUY) ? price + atr*ATR_TP_Mult : price - atr*ATR_TP_Mult;
   sl = NormalizeDouble(sl, digs);
   tp = NormalizeDouble(tp, digs);

   int ticket = OrderSend(symbol, orderType, lotSize, price, 3, sl, tp,
                          "Currency Dashboard - "+symbol, MagicNumber, 0, clrNONE);
   if(ticket > 0)
      Print("Order #",ticket," opened: ",(orderType==OP_BUY?"BUY":"SELL")," ",symbol,
            " lots:",lotSize," price:",price," SL:",sl," TP:",tp);
   else
   {
      Print("OrderSend failed for ",symbol," Error: ",GetLastError(),". Retry without SL/TP...");
      ticket = OrderSend(symbol, orderType, lotSize, price, 3, 0, 0,
                         "Currency Dashboard - "+symbol, MagicNumber, 0, clrNONE);
      if(ticket > 0)
      {
         // Apply SL/TP via OrderModify
         if(OrderSelect(ticket, SELECT_BY_TICKET))
         {
            double op = OrderOpenPrice();
            sl = (orderType==OP_BUY) ? op - atr*ATR_SL_Mult : op + atr*ATR_SL_Mult;
            tp = (orderType==OP_BUY) ? op + atr*ATR_TP_Mult : op - atr*ATR_TP_Mult;
            sl = NormalizeDouble(sl,digs); tp = NormalizeDouble(tp,digs);
            for(int att=1; att<=5; att++)
            {
               if(OrderModify(ticket, op, sl, tp, 0, clrNONE)) break;
               Sleep(200);
            }
         }
      }
      else Print("OrderSend retry failed for ",symbol," Error: ",GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Trailing Stop functions                                          |
//+------------------------------------------------------------------+
void InitializeTrailingStops()
{
   ArrayResize(trailingStops, 0);
   totalTrailingStops = 0;
}

int GetTrailingStopIndex(int ticket)
{
   for(int i=0; i<totalTrailingStops; i++) if(trailingStops[i].ticket==ticket) return i;
   return -1;
}

void UpdateTrailingStopDataWithLock(int ticket, double highestProfit, double lockLevel, bool isActive)
{
   int index = GetTrailingStopIndex(ticket);
   if(index < 0)
   {
      totalTrailingStops++;
      ArrayResize(trailingStops, totalTrailingStops);
      index = totalTrailingStops-1;
      trailingStops[index].ticket = ticket;
   }
   trailingStops[index].highestProfit    = highestProfit;
   trailingStops[index].currentLockLevel = lockLevel;
   trailingStops[index].isActive         = isActive;
}

void RemoveTrailingStopData(int ticket)
{
   int index = GetTrailingStopIndex(ticket);
   if(index < 0) return;
   for(int i=index; i<totalTrailingStops-1; i++) trailingStops[i]=trailingStops[i+1];
   totalTrailingStops--;
   ArrayResize(trailingStops, totalTrailingStops);
}

double CalculateLockLevel(double highestProfit)
{
   if(highestProfit < TrailingStartProfit) return 0.0;
   double lockLevel = highestProfit * TrailingLockRatio;
   return MathRound(lockLevel/TrailingStepSize)*TrailingStepSize;
}

void ManageTrailingStops()
{
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber) continue;
      if(OrderType()!=OP_BUY && OrderType()!=OP_SELL) continue;

      int ticket = OrderTicket();
      string symbol = OrderSymbol();
      int orderType = OrderType();
      double currentProfit = OrderProfit()+OrderSwap()+OrderCommission();
      if(currentProfit < 0) continue;

      int tsIndex = GetTrailingStopIndex(ticket);
      bool isActive = false;
      double highestProfit = currentProfit, currentLockLevel = 0.0;
      if(tsIndex >= 0)
      {
         isActive         = trailingStops[tsIndex].isActive;
         highestProfit    = trailingStops[tsIndex].highestProfit;
         currentLockLevel = trailingStops[tsIndex].currentLockLevel;
      }

      if(!isActive && currentProfit >= TrailingStartProfit)
      {
         isActive = true;
         highestProfit = currentProfit;
         currentLockLevel = CalculateLockLevel(highestProfit);
         UpdateTrailingStopDataWithLock(ticket, highestProfit, currentLockLevel, isActive);
      }

      if(isActive)
      {
         if(currentProfit > highestProfit)
         {
            highestProfit = currentProfit;
            currentLockLevel = CalculateLockLevel(highestProfit);
            UpdateTrailingStopDataWithLock(ticket, highestProfit, currentLockLevel, isActive);
         }
         if(currentProfit < currentLockLevel)
         {
            double closePrice = (orderType==OP_BUY) ? SymbolInfoDouble(symbol,SYMBOL_BID) : SymbolInfoDouble(symbol,SYMBOL_ASK);
            color  arrowColor = (orderType==OP_BUY) ? clrRed : clrBlue;
            if(OrderClose(ticket, OrderLots(), closePrice, 3, arrowColor))
            {
               Print("Trailing Stop LOCKED PROFIT #",ticket," ",symbol,
                     " | Highest: $",DoubleToString(highestProfit,2),
                     " | Lock: $",DoubleToString(currentLockLevel,2));
               RemoveTrailingStopData(ticket);
            }
         }
      }
   }
   CleanupTrailingStopData();
}

void CleanupTrailingStopData()
{
   for(int i=totalTrailingStops-1; i>=0; i--)
   {
      bool orderExists = false;
      if(OrderSelect(trailingStops[i].ticket, SELECT_BY_TICKET))
         if(OrderCloseTime()==0) orderExists=true;
      if(!orderExists) RemoveTrailingStopData(trailingStops[i].ticket);
   }
}
//+------------------------------------------------------------------+
