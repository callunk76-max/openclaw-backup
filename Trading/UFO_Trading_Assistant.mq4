//+------------------------------------------------------------------+
//|                                              UFO_Trading_Assistant.mq4 |
//|                                          Dwiyan Anggara Style      |
//+------------------------------------------------------------------+
#property copyright "UFO Trading Assistant [Cuy]"
#property link      ""
#property version   "3.00"
#property description "UFO Trading Assistant — Auto SL/TP Manager"
#property description "Mode AUTO: deteksi zone + entry otomatis"
#property description "Mode MANUAL: panel BUY/SELL + manajemen posisi"
#property strict

// ── SETTINGS ────────────────────────────────────────────────────
input string   ___SETTINGS___          = "═══ PENGATURAN ═══";
input bool     AutoManageNewTrades     = true;
input double   RiskRewardRatio         = 2.0;
input bool     UseFixedSL              = false;
input int      FixedSLPoints           = 500;
input int      Slippage                = 30;

input string   ___ZONE___              = "═══ UFO ZONE ═══";
input int      MaxBaseCandles          = 5;
input double   LegOutMultiplier        = 1.5;
input int      ZoneExpiryBars          = 50;
input bool     ShowZones               = true;
input int      ScanBarsCount           = 500;

input string   ___RISK___              = "═══ RISK ═══";
input double   RiskPercent             = 2.0;
input bool     UseFixedLot             = false;
input double   FixedLot                = 0.01;

input string   ___ADV___               = "═══ ADVANCED ═══";
input int      MagicNumber             = 891202720;
input int      PanelX                  = 5;
input int      PanelY                  = 5;
input color    PanelBg                 = C'20,25,45';

// ── CONSTANTS ──────────────────────────────────────────────────
string LBL = "UFO_";

// ── STRUCTS ────────────────────────────────────────────────────
struct UFOZone
{
   double   proximal, distal, zoneHigh, zoneLow, zoneWidth;
   bool     isDemand, active, emaOk, trendOk;
   string   pattern;
   int      barCreated, score, scoreA, scoreB, touchCount;
};

UFOZone zones[];
int zoneCount = 0;

// ── GLOBALS ────────────────────────────────────────────────────
bool    AutoMode     = false;
bool    ScanDone     = false;
int     scanPointer  = 0;
int     LastBuyBar   = 0;
int     LastSellBar  = 0;
int     baseCount    = 0;
double  baseLowest=0, baseHighest=0, legInHigh=0, legInLow=0;
double  RuntimeRR    = 2.0;  // runtime copy of RiskRewardRatio

//+------------------------------------------------------------------+
//| Helper: Create label                                              |
//+------------------------------------------------------------------+
void ufoLabel(string name, string text, int x, int y, color clr, int sz=8)
{
   string nm = LBL+name;
   if(ObjectFind(0,nm) < 0)
   {
      ObjectCreate(0, nm, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, nm, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, nm, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
      ObjectSetString(0, nm, OBJPROP_FONT, "Segoe UI");
   }
   ObjectSetInteger(0, nm, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, nm, OBJPROP_YDISTANCE, y);
   ObjectSetString(0, nm, OBJPROP_TEXT, text);
   ObjectSetInteger(0, nm, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, nm, OBJPROP_FONTSIZE, sz);
}

//+------------------------------------------------------------------+
//| Helper: Create button                                             |
//+------------------------------------------------------------------+
void ufoBtn(string name, string text, int x, int y, int w, int h, color bg, color txtClr)
{
   string nm = LBL+name;
   if(ObjectFind(0,nm) < 0)
   {
      ObjectCreate(0, nm, OBJ_BUTTON, 0, 0, 0);
      ObjectSetInteger(0, nm, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, nm, OBJPROP_SELECTABLE, true);
      ObjectSetInteger(0, nm, OBJPROP_BACK, false);
      ObjectSetString(0, nm, OBJPROP_FONT, "Segoe UI");
   }
   ObjectSetInteger(0, nm, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, nm, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, nm, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, nm, OBJPROP_YSIZE, h);
   ObjectSetString(0, nm, OBJPROP_TEXT, text);
   ObjectSetInteger(0, nm, OBJPROP_COLOR, txtClr);
   ObjectSetInteger(0, nm, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, nm, OBJPROP_BORDER_COLOR, C'80,90,120');
   ObjectSetInteger(0, nm, OBJPROP_FONTSIZE, 8);
}

//+------------------------------------------------------------------+
//| Helper: Update button text/color                                  |
//+------------------------------------------------------------------+
void ufoBtnSet(string name, string text, color bg, color txtClr)
{
   string nm = LBL+name;
   ObjectSetString(0, nm, OBJPROP_TEXT, text);
   ObjectSetInteger(0, nm, OBJPROP_COLOR, txtClr);
   ObjectSetInteger(0, nm, OBJPROP_BGCOLOR, bg);
}
void ufoLblSet(string name, string text, color clr)
{
   string nm = LBL+name;
   ObjectSetString(0, nm, OBJPROP_TEXT, text);
   ObjectSetInteger(0, nm, OBJPROP_COLOR, clr);
}

//+------------------------------------------------------------------+
//| Create panel                                                      |
//+------------------------------------------------------------------+
void CreatePanel()
{
   int x=PanelX, y=PanelY, m=4, bw=150;
   ufoLabel("Tt", "UFO", x+m, y+2, clrGold, 9);
   ufoBtn("BA", "AUTO:OFF", x+m, y+20, bw, 20, C'60,60,60', clrGray);
   int hw=(bw-2)/2;
   ufoBtn("BB", "BUY", x+m, y+44, hw, 20, clrDarkGreen, clrWhite);
   ufoBtn("BS", "SELL", x+m+hw+2, y+44, hw, 20, C'139,0,0', clrWhite);
   ufoBtn("BR", "RR 1:2", x+m, y+68, bw, 18, C'30,35,60', clrWhite);
   ufoBtn("BC", "CLOSE ALL", x+m, y+90, bw, 18, C'80,20,20', clrWhite);
   ufoLabel("I1", "0B/0S Z:0", x+m, y+116, clrSilver, 7);
   ufoLabel("I2", "$0.00", x+m, y+132, clrSilver, 7);
   ufoLabel("I3", "0.0p", x+m, y+148, clrWhite, 8);
   ufoLabel("I4", "$10000", x+m, y+164, clrSilver, 7);
}

//+------------------------------------------------------------------+
//| Update panel info                                                 |
//+------------------------------------------------------------------+
void UpdPanel()
{
   int bc=0, sc=0; double pf=0, pp=0;
   for(int i=OrdersTotal()-1; i>=0; i--)
   {
      if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES)) continue;
      if(OrderMagicNumber()!=MagicNumber || OrderSymbol()!=Symbol()) continue;
      if(OrderType()==OP_BUY) { bc++; pp+=(Bid-OrderOpenPrice())/Point/10; }
      else if(OrderType()==OP_SELL) { sc++; pp+=(OrderOpenPrice()-Ask)/Point/10; }
      pf+=OrderProfit()+OrderSwap()+OrderCommission();
   }
   ufoBtnSet("BA", AutoMode?"AUTO:ON":"AUTO:OFF", AutoMode?C'0,100,50':C'60,60,60', AutoMode?clrLime:clrGray);
   ufoBtnSet("BR", "RR 1:"+DoubleToString(RuntimeRR,1), C'30,35,60', clrWhite);
   ufoLblSet("I1", IntegerToString(bc)+"B/"+IntegerToString(sc)+"S Z:"+IntegerToString(zoneCount), clrSilver);
   ufoLblSet("I2", "$"+DoubleToString(pf,2), clrSilver);
   ufoLblSet("I3", (pp>=0?"+":"")+DoubleToString(pp,1)+"p", pp>=0?clrPaleGreen:clrLightCoral);
   ufoLblSet("I4", "$"+DoubleToString(AccountBalance(),2), clrSilver);
}

//+------------------------------------------------------------------+
//| OnInit                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   zoneCount=0; ArrayResize(zones,200); ScanDone=false; scanPointer=1; RuntimeRR=RiskRewardRatio;
   CreatePanel();
   Print("UFO loaded. Scanning ", ScanBarsCount, " bars...");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   // Delete all UFO chart objects
   for(int i=0; i<200; i++)
   {
      ObjectDelete(0, LBL+"ZP"+IntegerToString(i));
      ObjectDelete(0, LBL+"ZD"+IntegerToString(i));
      ObjectDelete(0, LBL+"ZL"+IntegerToString(i));
   }
   // Delete panel objects
   ObjectDelete(0, LBL+"Tt"); ObjectDelete(0, LBL+"BA");
   ObjectDelete(0, LBL+"BB"); ObjectDelete(0, LBL+"BS");
   ObjectDelete(0, LBL+"BR"); ObjectDelete(0, LBL+"BC");
   ObjectDelete(0, LBL+"I1"); ObjectDelete(0, LBL+"I2");
   ObjectDelete(0, LBL+"I3"); ObjectDelete(0, LBL+"I4");
}

//+------------------------------------------------------------------+
//| Bar processing                                                    |
//+------------------------------------------------------------------+
void ProcessBar(int bar)
{
   if(Bars<20 || bar<1) return;
   double atr=iATR(Symbol(),0,14,bar); if(atr<=0) atr=200*Point;
   double range=High[bar]-Low[bar];
   bool isBase=range<atr*1.0;
   if(isBase)
   {
      if(baseCount==0) { baseLowest=Low[bar]; baseHighest=High[bar]; legInHigh=High[iHighest(NULL,0,MODE_HIGH,10,bar+1)]; legInLow=Low[iLowest(NULL,0,MODE_LOW,10,bar+1)]; baseCount=1; }
      else { baseLowest=MathMin(baseLowest,Low[bar]); baseHighest=MathMax(baseHighest,High[bar]); baseCount++; }
   }
   else
   {
      if(baseCount>=1 && baseCount<=MaxBaseCandles)
      {
         double br=baseHighest-baseLowest, lo=High[bar]-Low[bar];
         bool vB=lo>br;
         if(vB && br>0)
         {
            bool rB4=legInHigh>baseHighest, dB4=legInLow<baseLowest, rAf=High[bar]>baseHighest, dAf=Low[bar]<baseLowest;
            bool isRBR=rB4&&rAf, isDBD=dB4&&dAf, isRBD=rB4&&dAf, isDBR=dB4&&rAf;
            if(zoneCount<200 && (isRBR||isDBR||isDBD||isRBD))
            {
               double buf=atr*0.1;
               zones[zoneCount].proximal=(isRBR||isDBR)?baseHighest+buf:baseLowest-buf;
               zones[zoneCount].distal=(isRBR||isDBR)?baseLowest-buf:baseHighest+buf;
               zones[zoneCount].isDemand=(isRBR||isDBR);
               zones[zoneCount].pattern=isRBR?"RBR":isDBR?"DBR":isDBD?"DBD":"RBD";
               zones[zoneCount].barCreated=bar;
               zones[zoneCount].score=(int)(lo/(br>0?br:1)*3); if(zones[zoneCount].score>10) zones[zoneCount].score=10;
               zones[zoneCount].active=true; zones[zoneCount].touchCount=0;
               zones[zoneCount].zoneWidth=br;
               zoneCount++;
            }
         }
      }
      baseCount=0; baseLowest=0; baseHighest=0;
   }
}

//+------------------------------------------------------------------+
//| Render zones                                                      |
//+------------------------------------------------------------------+
void RenderZones()
{
   // Clean old zone objects
   for(int i=0; i<200; i++)
   {
      ObjectDelete(0, LBL+"ZP"+IntegerToString(i));
      ObjectDelete(0, LBL+"ZD"+IntegerToString(i));
      ObjectDelete(0, LBL+"ZL"+IntegerToString(i));
   }
   for(int i=0; i<zoneCount; i++)
   {
      if(!zones[i].active) continue;
      int age=Bars-zones[i].barCreated;
      if(age>ZoneExpiryBars || age<0) continue;
      color zc=zones[i].isDemand?clrLime:clrRed;
      string pi=LBL+"ZP"+IntegerToString(i), di=LBL+"ZD"+IntegerToString(i), li=LBL+"ZL"+IntegerToString(i);
      if(ObjectFind(0,pi)<0) { ObjectCreate(0,pi,OBJ_HLINE,0,0,zones[i].proximal); ObjectSetInteger(0,pi,OBJPROP_WIDTH,2); ObjectSetInteger(0,pi,OBJPROP_BACK,false); }
      if(ObjectFind(0,di)<0) { ObjectCreate(0,di,OBJ_HLINE,0,0,zones[i].distal); ObjectSetInteger(0,di,OBJPROP_STYLE,STYLE_DOT); ObjectSetInteger(0,di,OBJPROP_BACK,false); }
      ObjectSetDouble(0,pi,OBJPROP_PRICE,0,zones[i].proximal);
      ObjectSetDouble(0,di,OBJPROP_PRICE,0,zones[i].distal);
      ObjectSetInteger(0,pi,OBJPROP_COLOR,zc); ObjectSetInteger(0,di,OBJPROP_COLOR,zc);
      // Label
      if(ObjectFind(0,li)<0) { ObjectCreate(0,li,OBJ_LABEL,0,0,0); ObjectSetString(0,li,OBJPROP_FONT,"Segoe UI"); ObjectSetInteger(0,li,OBJPROP_FONTSIZE,8); }
      string lbl=zones[i].pattern+" S:"+IntegerToString(zones[i].score);
      double lx=zones[i].isDemand?zones[i].proximal:zones[i].distal;
      ObjectSetString(0,li,OBJPROP_TEXT,lbl+" ");
      ObjectSetInteger(0,li,OBJPROP_COLOR,zc);
      ObjectSetDouble(0,li,OBJPROP_PRICE,0,lx);
   }
}

//+------------------------------------------------------------------+
//| OnTick                                                            |
//+------------------------------------------------------------------+
void OnTick()
{
   // Gradual scan
   if(!ScanDone)
   {
      int end=MathMin(scanPointer+39, MathMin(ScanBarsCount, Bars-2));
      for(int hb=end; hb>=scanPointer; hb--) ProcessBar(hb);
      scanPointer=end+1;
      if(scanPointer>=MathMin(ScanBarsCount,Bars-2)) { ScanDone=true; Print("UFO done: ",zoneCount," zones"); if(ShowZones) RenderZones(); UpdPanel(); ChartRedraw(); }
      return;
   }

   // New bar
   static datetime lst=0;
   bool nb=(lst!=Time[0]);
   if(nb) { lst=Time[0]; ProcessBar(1); RenderZones(); UpdPanel(); ChartRedraw(); }
}

//+------------------------------------------------------------------+
//| OnChartEvent                                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lp, const double &dp, const string &sp)
{
   if(id!=CHARTEVENT_OBJECT_CLICK) return;
   ObjectSetInteger(0,sp,OBJPROP_SELECTED,false);

   if(sp==LBL+"BA") { AutoMode=!AutoMode; UpdPanel(); return; }
   if(sp==LBL+"BB") { ExecuteBuy(); return; }
   if(sp==LBL+"BS") { ExecuteSell(); return; }
   if(sp==LBL+"BR")
   {
      if(RuntimeRR>=3) RuntimeRR=1;
      else if(RuntimeRR>=2) RuntimeRR=3;
      else RuntimeRR=2;
      UpdPanel(); return;
   }
   if(sp==LBL+"BC")
   {
      for(int i=OrdersTotal()-1; i>=0; i--)
         if(OrderSelect(i,SELECT_BY_POS,MODE_TRADES) && OrderSymbol()==Symbol() && OrderMagicNumber()==MagicNumber)
            { if(OrderType()==OP_BUY) OrderClose(OrderTicket(),OrderLots(),Bid,Slippage,clrWhite); else if(OrderType()==OP_SELL) OrderClose(OrderTicket(),OrderLots(),Ask,Slippage,clrWhite); }
      return;
   }
}

//+------------------------------------------------------------------+
//| Manual BUY                                                        |
//+------------------------------------------------------------------+
void ExecuteBuy()
{
   double lot=CalcLot(); if(lot<=0) return;
   double atr=iATR(Symbol(),0,14,0); if(atr<=0) atr=200*Point;
   double sl=NormalizeDouble(Ask-atr*0.5,Digits), tp=NormalizeDouble(Ask+atr*RuntimeRR*0.5,Digits);
   int t=OrderSend(Symbol(),OP_BUY,lot,Ask,Slippage,sl,tp,"[UFO]Buy",MagicNumber,0,clrGreen);
   if(t<0) Print("Buy err:",GetLastError());
}

//+------------------------------------------------------------------+
//| Manual SELL                                                       |
//+------------------------------------------------------------------+
void ExecuteSell()
{
   double lot=CalcLot(); if(lot<=0) return;
   double atr=iATR(Symbol(),0,14,0); if(atr<=0) atr=200*Point;
   double sl=NormalizeDouble(Bid+atr*0.5,Digits), tp=NormalizeDouble(Bid-atr*RuntimeRR*0.5,Digits);
   int t=OrderSend(Symbol(),OP_SELL,lot,Bid,Slippage,sl,tp,"[UFO]Sell",MagicNumber,0,clrRed);
   if(t<0) Print("Sell err:",GetLastError());
}

//+------------------------------------------------------------------+
//| Lot calculator                                                    |
//+------------------------------------------------------------------+
double CalcLot()
{
   if(UseFixedLot) return FixedLot;
   double risk=AccountBalance()*RiskPercent/100;
   double atr=iATR(Symbol(),0,14,0); if(atr<=0) atr=200*Point;
   double slPts=atr*0.5/Point; if(slPts<=0) slPts=100;
   double tv=MarketInfo(Symbol(),MODE_TICKVALUE); if(tv<=0) tv=1;
   double lot=risk/(slPts*tv*10);
   double ls=MarketInfo(Symbol(),MODE_LOTSTEP);
   lot=MathFloor(lot/ls)*ls; lot=MathMax(MarketInfo(Symbol(),MODE_MINLOT),MathMin(lot,MarketInfo(Symbol(),MODE_MAXLOT)));
   return lot;
}
//+------------------------------------------------------------------+
