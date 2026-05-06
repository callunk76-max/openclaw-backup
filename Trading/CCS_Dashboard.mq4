//+------------------------------------------------------------------+
//|                                               CCS_Dashboard.mq4  |
//|          Callunk Confluence System — EA Dashboard Multi Pair      |
//|                                        Callunk & Cuy              |
//+------------------------------------------------------------------+
#property copyright "Callunk & Cuy"
#property version   "1.04"
#property strict
#property description "CCS Dashboard — 29 Pair EA | Klik header RSI/VOL/SnR/BB utk toggle"
#property description "Klik F+/F- utk ubah ukuran font & layout"

input int    FontSize     =  8;
input color  TextColor    = clrWhite;
input color  HeaderColor  = clrYellow;
input int    StartX       = 10;
input int    StartY       = 25;
input string CustomPairs  = "AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY,XAUUSD";
input double LotSize             = 0.01;
input int    MagicNumber         = 20260506;
input int    MaxOpenPositions    = 3;
input int    Slippage            = 10;
input double ATR_SL_Mult         = 1.5;
input double ATR_TP_Mult         = 2.0;
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
input double CS_Strong_Threshold = 5.0;

string pairs[]; int totalPairs;
bool autoTradeON=false, alertON=true;
int runtimeMaxPos=0, runtimeFontSize=8;
datetime lastUpdateTime=0; int updateCounter=0;

struct CCSData {
   string pair; int signal, prevSignal, gateBull, gateBear;
   double rsi, atr, ccyGap; int score;
   bool bbTouchLow, bbTouchHigh, atrNaik;
   string regime, warning, nearestSup, nearestRes;
};
CCSData ccsData[];
string lastAlertSignal[]; datetime lastAlertTime[];

bool tog_RSI=false, tog_VOL=false, tog_SnR=false, tog_BB=false;

struct TrailData { int ticket; double peak; bool active; };
TrailData trailData[]; int trailCount=0;

string ccyList[8]={"USD","EUR","GBP","CHF","CAD","AUD","JPY","NZD"};
int ccyIdx(string c){for(int i=0;i<8;i++)if(ccyList[i]==c)return i;return -1;}
color RGB(int r,int g,int b){return(color)((r&0xFF)|((g&0xFF)<<8)|((b&0xFF)<<16));}

int OnInit(){
   runtimeMaxPos=MaxOpenPositions; runtimeFontSize=FontSize;
   string s=CustomPairs; StringReplace(s," ","");
   totalPairs=1; for(int i=0;i<StringLen(s);i++)if(StringGetCharacter(s,i)==',')totalPairs++;
   ArrayResize(pairs,totalPairs);
   int start=0,idx=0;
   for(int i=0;i<=StringLen(s);i++){
      if(i==StringLen(s)||StringGetCharacter(s,i)==','){if(i>start){string p=StringSubstr(s,start,i-start);if(StringLen(p)>0)pairs[idx++]=p;}start=i+1;}
   }
   totalPairs=idx; ArrayResize(pairs,totalPairs);
   ArrayResize(ccsData,totalPairs); ArrayResize(lastAlertSignal,totalPairs); ArrayResize(lastAlertTime,totalPairs);
   for(int i=0;i<totalPairs;i++){ccsData[i].prevSignal=0;lastAlertSignal[i]="";lastAlertTime[i]=0;}
   ArrayResize(trailData,50); trailCount=0;
   CreateDashboard(); EventSetTimer(1); return INIT_SUCCEEDED;
}
void OnDeinit(const int r){EventKillTimer();DeleteAllObjects();}

void OnTick(){
   datetime n=TimeCurrent();if(n==lastUpdateTime)return;lastUpdateTime=n;updateCounter++;
   UpdateAllSignals();if(updateCounter%2==0&&autoTradeON)RunAutoTrade();
   ManageTrailingStops();UpdateDashboard();
}
void OnTimer(){
   datetime n=TimeCurrent();if(n==lastUpdateTime)return;lastUpdateTime=n;updateCounter++;
   UpdateAllSignals();if(updateCounter%2==0){CheckAlerts();if(autoTradeON)RunAutoTrade();}
   ManageTrailingStops();UpdateDashboard();
}

void OnChartEvent(const int id,const long&lparam,const double&dparam,const string&sparam){
   if(id!=CHARTEVENT_OBJECT_CLICK)return;
   if(sparam=="BtnAutoTrade"){autoTradeON=!autoTradeON;UpdateAutoTradeBtn();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="BtnAlert"){alertON=!alertON;UpdateAlertBtn();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HeaderCloseAll"){CloseAllPositions();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="BtnFontMinus"){ResizeFont(runtimeFontSize-1);ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="BtnFontPlus"){ResizeFont(runtimeFontSize+1);ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   // Header toggles
   if(sparam=="HDR_RSI"){tog_RSI=!tog_RSI;UpdateHDRToggles();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_VOL"){tog_VOL=!tog_VOL;UpdateHDRToggles();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_SnR"){tog_SnR=!tog_SnR;UpdateHDRToggles();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_BB"){tog_BB=!tog_BB;UpdateHDRToggles();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   // Buttons per pair
   if(StringFind(sparam,"BtnBuy_")==0){int i=(int)StringToInteger(StringSubstr(sparam,7));if(i>=0&&i<totalPairs){OpenTrade(pairs[i],OP_BUY);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"BtnSell_")==0){int i=(int)StringToInteger(StringSubstr(sparam,8));if(i>=0&&i<totalPairs){OpenTrade(pairs[i],OP_SELL);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"BtnClose_")==0){int i=(int)StringToInteger(StringSubstr(sparam,9));if(i>=0&&i<totalPairs){CloseSymbol(pairs[i]);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"MaxMinus")==0){if(runtimeMaxPos>1)runtimeMaxPos--;UpdateMaxOrder();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"MaxPlus")==0){if(runtimeMaxPos<10)runtimeMaxPos++;UpdateMaxOrder();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
}

// ===== RESIZE =====
void ResizeFont(int n){if(n<6||n>22)return;runtimeFontSize=n;DeleteAllObjects();CreateDashboard();ChartRedraw();}

// ===== SIGNALS =====
void UpdateAllSignals(){
   CalcCurrencyStrength();
   for(int i=0;i<totalPairs;i++){
      int raw=CalculateCCS_Signal(pairs[i],i);
      int pv=ccsData[i].prevSignal;
      int os=raw;
      if(pv>=2&&raw<=-1)os=0; if(pv<=-2&&raw>=1)os=0;
      if(pv>=1&&raw<=-2)os=0; if(pv<=-1&&raw>=2)os=0;
      if(pv==2&&raw==0)os=1; if(pv==-2&&raw==0)os=-1;
      ccsData[i].prevSignal=os; ccsData[i].signal=os;
   }
}

// ===== CURRENCY STRENGTH =====
double ccyStrength[8]={0,0,0,0,0,0,0,0};
void CalcCurrencyStrength(){
   double s[28]; string p[28]={"GBPUSD","USDCHF","EURUSD","USDJPY","USDCAD","NZDUSD","AUDUSD","AUDNZD","AUDCAD","AUDCHF","AUDJPY","CADJPY","CHFJPY","EURGBP","EURAUD","EURCHF","EURJPY","EURNZD","EURCAD","GBPCHF","GBPAUD","GBPCAD","GBPJPY","GBPNZD","NZDJPY","NZDCAD","CHFCAD","NZDCHF"};
   for(int i=0;i<28;i++){
      double dc=iClose(p[i],PERIOD_D1,0), dh=iHigh(p[i],PERIOD_D1,0), dl=iLow(p[i],PERIOD_D1,0);
      if(dh<=dl||dc<=0){s[i]=-1;continue;}
      double r=(dc-dl)/(dh-dl);
      if(r>=0.97)s[i]=9;else if(r>=0.90)s[i]=8;else if(r>=0.75)s[i]=7;else if(r>=0.60)s[i]=6;else if(r>=0.50)s[i]=5;else if(r>=0.40)s[i]=4;else if(r>=0.25)s[i]=3;else if(r>=0.10)s[i]=2;else if(r>=0.03)s[i]=1;else s[i]=0;
   }
   double su[8]; su[0]=((9-s[0])+s[1]+(9-s[2])+s[3]+s[4]+(9-s[5])+(9-s[6]))/7.0;
   su[1]=(s[2]+s[13]+s[14]+s[15]+s[16]+s[17]+s[18])/7.0;
   su[2]=(s[0]+(9-s[13])+s[19]+s[20]+s[21]+s[22]+s[23])/7.0;
   su[3]=((9-s[1])+(9-s[9])+s[12]+(9-s[15])+(9-s[19])+s[26]+(9-s[27]))/7.0;
   su[4]=((9-s[4])+(9-s[8])+s[11]+(9-s[18])+(9-s[21])+(9-s[25])+(9-s[26]))/7.0;
   su[5]=(s[6]+s[7]+s[8]+s[9]+s[10]+(9-s[14])+(9-s[20]))/7.0;
   su[6]=((9-s[3])+(9-s[10])+(9-s[11])+(9-s[12])+(9-s[16])+(9-s[22])+(9-s[24]))/7.0;
   su[7]=(s[5]+(9-s[7])+(9-s[17])+(9-s[23])+s[24]+s[25]+s[27])/7.0;
   for(int ci=0;ci<8;ci++)ccyStrength[ci]=su[ci];
}
double GetCCYGap(string sym){
   string b="",q="";
   if(sym=="XAUUSD"){b="XAU";q="USD";}else if(StringLen(sym)==6){b=StringSubstr(sym,0,3);q=StringSubstr(sym,3,3);}else return 0;
   int bi=ccyIdx(b),qi=ccyIdx(q); if(bi<0||qi<0)return 0;
   return NormalizeDouble(ccyStrength[bi]-ccyStrength[qi],1);
}

// ===== CCS SIGNAL =====
int CalculateCCS_Signal(string sym,int idx){
   if(MarketInfo(sym,MODE_BID)<=0)return 0;
   double c=iClose(sym,PERIOD_H1,0), e20=iMA(sym,PERIOD_H1,20,0,MODE_EMA,PRICE_CLOSE,0);
   double e50=iMA(sym,PERIOD_H1,50,0,MODE_EMA,PRICE_CLOSE,0), e100=iMA(sym,PERIOD_H1,100,0,MODE_EMA,PRICE_CLOSE,0);
   double e200=iMA(sym,PERIOD_H1,200,0,MODE_EMA,PRICE_CLOSE,0);
   double bl=iBands(sym,PERIOD_H1,BB_Period,BB_Deviation,0,PRICE_CLOSE,MODE_LOWER,0);
   double bu=iBands(sym,PERIOD_H1,BB_Period,BB_Deviation,0,PRICE_CLOSE,MODE_UPPER,0);
   double r=iRSI(sym,PERIOD_H1,RSI_Period,PRICE_CLOSE,0), rp=iRSI(sym,PERIOD_H1,RSI_Period,PRICE_CLOSE,1);
   double at=iATR(sym,PERIOD_H1,ATR_Period,0), atp=iATR(sym,PERIOD_H1,ATR_Period,10);
   double hh=iHigh(sym,PERIOD_H1,0), ll=iLow(sym,PERIOD_H1,0);
   ccsData[idx].ccyGap=GetCCYGap(sym);
   ccsData[idx].rsi=r; ccsData[idx].atr=at;
   ccsData[idx].bbTouchLow=(bl>0&&ll<=bl); ccsData[idx].bbTouchHigh=(bu>0&&hh>=bu);
   if(c==0||r==0)return 0;
   int gb=0,gs=0;
   if(e20>0&&c>e20)gb++;else if(e20>0&&c<e20)gs++;
   if(e50>0&&c>e50)gb++;else if(e50>0&&c<e50)gs++;
   if(e100>0&&c>e100)gb++;else if(e100>0&&c<e100)gs++;
   if(e200>0&&c>e200)gb++;else if(e200>0&&c<e200)gs++;
   ccsData[idx].gateBull=gb; ccsData[idx].gateBear=gs;
   double ns=0,nr=0,nsD=999999,nrD=999999;
   int bars=MathMin(200,iBars(sym,PERIOD_H1));
   if(bars>=SnR_BarsLeft+SnR_BarsRight+1){
      for(int b=SnR_BarsLeft;b<bars-SnR_BarsRight;b++){
         double sh=iHigh(sym,PERIOD_H1,b),sl=iLow(sym,PERIOD_H1,b); bool isSH=true,isSL=true;
         for(int j=1;j<=SnR_BarsLeft;j++){if(sh<=iHigh(sym,PERIOD_H1,b+j))isSH=false;if(sl>=iLow(sym,PERIOD_H1,b+j))isSL=false;}
         for(int j=1;j<=SnR_BarsRight;j++){if(sh<=iHigh(sym,PERIOD_H1,b-j))isSH=false;if(sl>=iLow(sym,PERIOD_H1,b-j))isSL=false;}
         if(isSH==isSL)continue;
         if(isSH){double d=MathAbs(sh-c);if(c<sh&&d<nrD){nr=sh;nrD=d;}}
         if(isSL){double d=MathAbs(sl-c);if(c>sl&&d<nsD){ns=sl;nsD=d;}}
   }}
   double atS=(at>0)?at:1;
   bool nSup=(ns>0&&nsD<atS*1.5), nRes=(nr>0&&nrD<atS*1.5);
   bool rOs=(r>0&&r<RSI_Oversold), rOb=(r>RSI_Overbought);
   bool rTu=(r>rp&&rp<RSI_Oversold), rTd=(r<rp&&rp>RSI_Overbought);
   bool pv=(atp>0); bool aN=(pv&&at>atp), aT=(pv&&at<atp);
   ccsData[idx].atrNaik=aN;
   string vt="=Nor";
   if(aT)vt="Sta"; else if(aN)vt="Vol";
   ccsData[idx].regime=vt;
   double gap=ccsData[idx].ccyGap;
   bool gBull=(gap>=CS_Strong_Threshold), gBear=(gap<=-CS_Strong_Threshold);
   int bs=0,ss=0;
   if(gBull){
      if(gb>=4)bs+=3;else if(gb>=3)bs+=2;else if(gb>=2)bs+=1;
      if(tog_RSI){if(ccsData[idx].bbTouchLow&&rOs)bs+=1;else if(rTu)bs+=1;}
      if(tog_BB&&!tog_RSI){if(ccsData[idx].bbTouchLow)bs+=1;}
      if(tog_VOL){if(aT)bs+=1;else if(aN)bs-=1;}
      if(tog_SnR&&nSup)bs+=1;
      if(gap>=7.0)bs+=2; if(gs>gb)bs-=2;
   }else if(gBear){
      if(gs>=4)ss+=3;else if(gs>=3)ss+=2;else if(gs>=2)ss+=1;
      if(tog_RSI){if(ccsData[idx].bbTouchHigh&&rOb)ss+=1;else if(rTd)ss+=1;}
      if(tog_BB&&!tog_RSI){if(ccsData[idx].bbTouchHigh)ss+=1;}
      if(tog_VOL){if(aT)ss+=1;else if(aN)ss-=1;}
      if(tog_SnR&&nRes)ss+=1;
      if(gap<=-7.0)ss+=2; if(gb>gs)ss-=2;
   }else{ccsData[idx].warning="NoGAP";ccsData[idx].score=0;return 0;}
   string w="";
   if(aN&&r>70)w="VolTop";else if(aN&&r<30)w="VolBot";
   else if(ccsData[idx].bbTouchHigh&&rOb)w="OB+BB";else if(ccsData[idx].bbTouchLow&&rOs)w="OS+BB";
   else if(nRes&&gb>=3)w="~Res";else if(nSup&&gs>=3)w="~Sup";
   else if(atp>0&&at>atp*1.5)w="ATR+";
   ccsData[idx].warning=w;
   ccsData[idx].score=(bs>ss)?bs:(ss>bs)?-ss:0;
   if(bs>=7)return 2; if(bs>=4)return 1;
   if(ss>=7)return -2; if(ss>=4)return -1;
   return 0;
}

// ===== DASHBOARD =====
void CreateDashboard(){
   int x=StartX,y=StartY,fs=runtimeFontSize,useLH=(int)(fs*1.8+1);
   double cs=(double)fs/8.0; if(cs<1.0)cs=1.0;
   int c0=x, c1=c0+(int)(50*cs), c2=c1+(int)(55*cs), c3=c2+(int)(60*cs);
   int cScore=c3+(int)(35*cs);
   int c4=cScore+(int)(30*cs), c5=c4+(int)(55*cs), c6=c5+(int)(45*cs), c7=c6+(int)(35*cs), c8=c7+(int)(45*cs);
   int c9=c8+(int)(30*cs), c10=c9+(int)(30*cs), c11=c10+(int)(40*cs);
   int totalW=c11+(int)(10*cs), btnH=useLH-2; if(btnH<12)btnH=12;

   // ── HEADERS (GAP & GT = label; RSI/VOL/SnR/BB = button toggle) ──
   CreateLabel("H_Pair","PAIR",c0,y,HeaderColor,fs);
   CreateLabel("H_Profit","PL",c1,y,HeaderColor,fs);
   CreateLabel("H_Signal","SIG",c2,y,HeaderColor,fs);
   CreateLabel("H_Score","%",cScore,y,clrDodgerBlue,fs);
   CreateLabel("H_Gap","GAP",c4,y,HeaderColor,fs);
   CreateLabel("H_Gates","GT",c5,y,HeaderColor,fs);
   HDR_Toggle("HDR_RSI","RSI",c6,y,(int)(45*cs),useLH,fs,!tog_RSI);
   HDR_Toggle("HDR_VOL","VOL",c7,y,(int)(35*cs),useLH,fs,!tog_VOL);
   HDR_Toggle("HDR_SnR","SnR",c8,y,(int)(45*cs),useLH,fs,!tog_SnR);
   HDR_Toggle("HDR_BB","BB",c9,y,(int)(30*cs),useLH,fs,!tog_BB);
   CreateButton("HeaderCloseAll","CLOSE",c10,y-2,(int)(90*cs),18,clrGray,clrBlack);

   y+=useLH+5;
   for(int i=0;i<totalPairs;i++){
      int ry=y+i*useLH, ly=ry+1;
      ObjectCreate(0,"RowBG_"+IntegerToString(i),OBJ_RECTANGLE_LABEL,0,0,0);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_XDISTANCE,x);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_YDISTANCE,ry);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_XSIZE,totalW);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_YSIZE,useLH-1);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_BGCOLOR,RGB(35,35,35));
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_BORDER_COLOR,RGB(50,50,50));
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_BACK,true);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,"RowBG_"+IntegerToString(i),OBJPROP_HIDDEN,true);
      CreateLabel("Pair_"+IntegerToString(i),pairs[i],c0,ly,TextColor,fs);
      CreateLabel("Profit_"+IntegerToString(i),"--",c1,ly,clrGray,fs);
      CreateLabel("Signal_"+IntegerToString(i),"WAIT",c2,ly,clrGray,fs);
      CreateLabel("Score_"+IntegerToString(i),"",cScore,ly,clrGray,fs);
      CreateLabel("Gap_"+IntegerToString(i),"--",c4,ly,clrGray,fs);
      CreateLabel("Gates_"+IntegerToString(i),"--",c5,ly,clrGray,fs);
      CreateLabel("RSI_"+IntegerToString(i),"--",c6,ly,clrGray,fs);
      CreateLabel("Vol_"+IntegerToString(i),"--",c7,ly,clrGray,fs);
      CreateLabel("Warn_"+IntegerToString(i),"",c8,ly,clrGray,fs);
      CreateButton("BtnBuy_"+IntegerToString(i),"B",c9,ry+1,(int)(30*cs),btnH,clrForestGreen,clrWhite);
      CreateButton("BtnSell_"+IntegerToString(i),"S",c10,ry+1,(int)(30*cs),btnH,clrCrimson,clrWhite);
      CreateButton("BtnClose_"+IntegerToString(i),"NO",c11,ry+1,(int)(40*cs),btnH,clrGray,clrBlack);
   }
   int botY=y+(totalPairs+1)*useLH;
   CreateLabel("L_Max","MAX:",x,botY,HeaderColor,fs);
   CreateButton("MaxMinus","-",x+(int)(35*cs),botY-2,(int)(18*cs),(int)(14*cs),clrRed,clrWhite);
   CreateLabel("L_MaxVal",IntegerToString(runtimeMaxPos),x+(int)(55*cs),botY,clrLime,fs);
   CreateButton("MaxPlus","+",x+(int)(75*cs),botY-2,(int)(18*cs),(int)(14*cs),clrLime,clrBlack);
   int botY2=botY+useLH; int b=x;
   CreateLabel("L_Bal","BAL:",b,botY2,HeaderColor,fs); b+=(int)(35*cs);
   CreateLabel("L_BalVal","$0",b,botY2,clrLime,fs); b+=(int)(55*cs);
   CreateLabel("L_Margin","MAR:",b,botY2,HeaderColor,fs); b+=(int)(35*cs);
   CreateLabel("L_MarginVal","$0",b,botY2,clrLime,fs); b+=(int)(55*cs);
   CreateButton("BtnFontMinus","F-",b,botY2-2,(int)(22*cs),(int)(16*cs),clrGray,clrWhite); b+=(int)(28*cs);
   CreateLabel("L_FontVal","F:"+IntegerToString(runtimeFontSize),b,botY2,clrLightGray,fs); b+=(int)(35*cs);
   CreateButton("BtnFontPlus","F+",b,botY2-2,(int)(22*cs),(int)(16*cs),clrLime,clrBlack); b+=(int)(40*cs);
   CreateButton("BtnAutoTrade","AUTO:OFF",b,botY2-2,(int)(80*cs),(int)(16*cs),C'50,50,50',clrGray); b+=(int)(85*cs);
   CreateButton("BtnAlert","ALERT:ON",b,botY2-2,(int)(70*cs),(int)(16*cs),C'0,100,0',clrLime);
}

void HDR_Toggle(string n,string t,int x,int y,int w,int h,int fs,bool isOff){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x); ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w); ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetString(0,n,OBJPROP_TEXT,t);
   ObjectSetInteger(0,n,OBJPROP_COLOR,isOff?clrDimGray:clrYellow);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,clrBlack);
   ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,clrBlack);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,fs);
   ObjectSetString(0,n,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);
   ObjectSetInteger(0,n,OBJPROP_SELECTABLE,true);
   ObjectSetInteger(0,n,OBJPROP_SELECTED,false);
}

void UpdateHDRToggles(){
   ObjectSetInteger(0,"HDR_RSI",OBJPROP_COLOR,tog_RSI?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_VOL",OBJPROP_COLOR,tog_VOL?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_SnR",OBJPROP_COLOR,tog_SnR?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_BB", OBJPROP_COLOR,tog_BB?clrYellow:clrDimGray);
}

void UpdateDashboard(){
   for(int i=0;i<totalPairs;i++){
      string st="WAIT"; color sc=clrGray;
      switch(ccsData[i].signal){case 2:st="STRBUY";sc=clrLime;break;case 1:st="BUY";sc=clrMediumSeaGreen;break;case -1:st="SELL";sc=clrTomato;break;case -2:st="STRSEL";sc=clrRed;break;}
      ObjectSetString(0,"Signal_"+IntegerToString(i),OBJPROP_TEXT,st);
      ObjectSetInteger(0,"Signal_"+IntegerToString(i),OBJPROP_COLOR,sc);
      // Score %
      int rs=ccsData[i].score; int pct=(int)(MathAbs(rs)*100/10); if(pct>100)pct=100;
      color pcl=clrGray; if(rs>=7)pcl=clrLime;else if(rs>=4)pcl=clrMediumSeaGreen;else if(rs<=-7)pcl=clrRed;else if(rs<=-4)pcl=clrTomato;
      ObjectSetString(0,"Score_"+IntegerToString(i),OBJPROP_TEXT,IntegerToString(pct)+"%");
      ObjectSetInteger(0,"Score_"+IntegerToString(i),OBJPROP_COLOR,pcl);
      // GAP
      double gv=ccsData[i].ccyGap;
      ObjectSetString(0,"Gap_"+IntegerToString(i),OBJPROP_TEXT,DoubleToString(MathAbs(gv),1));
      ObjectSetInteger(0,"Gap_"+IntegerToString(i),OBJPROP_COLOR,(gv>=CS_Strong_Threshold)?clrLime:(gv<=-CS_Strong_Threshold)?clrRed:clrGray);
      // GT
      ObjectSetString(0,"Gates_"+IntegerToString(i),OBJPROP_TEXT,IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear));
      ObjectSetInteger(0,"Gates_"+IntegerToString(i),OBJPROP_COLOR,(ccsData[i].gateBull>ccsData[i].gateBear)?clrMediumSeaGreen:(ccsData[i].gateBear>ccsData[i].gateBull)?clrTomato:clrGray);
      // RSI
      ObjectSetString(0,"RSI_"+IntegerToString(i),OBJPROP_TEXT,DoubleToString(ccsData[i].rsi,1));
      double rv=ccsData[i].rsi;
      ObjectSetInteger(0,"RSI_"+IntegerToString(i),OBJPROP_COLOR,(rv>0&&rv<RSI_Oversold)?clrLime:(rv>RSI_Overbought)?clrRed:clrWhite);
      // VOL
      ObjectSetString(0,"Vol_"+IntegerToString(i),OBJPROP_TEXT,ccsData[i].regime);
      ObjectSetInteger(0,"Vol_"+IntegerToString(i),OBJPROP_COLOR,(ccsData[i].regime=="Sta")?clrLimeGreen:(ccsData[i].regime=="Vol")?clrOrange:clrGray);
      // WARN
      ObjectSetString(0,"Warn_"+IntegerToString(i),OBJPROP_TEXT,ccsData[i].warning);
      color wc2=clrGray;
      if(StringFind(ccsData[i].warning,"Vol")==0||StringFind(ccsData[i].warning,"OB+")==0||StringFind(ccsData[i].warning,"OS+")==0)wc2=clrRed;
      else if(StringLen(ccsData[i].warning)>0)wc2=clrOrange;
      ObjectSetInteger(0,"Warn_"+IntegerToString(i),OBJPROP_COLOR,wc2);
      // PROFIT + CLOSE
      double prof=0; int oc=0; bool hB=false,hS=false;
      for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=pairs[i]||OrderMagicNumber()!=MagicNumber)continue;prof+=OrderProfit()+OrderSwap()+OrderCommission();oc++;if(OrderType()==OP_BUY)hB=true;if(OrderType()==OP_SELL)hS=true;}
      ObjectSetString(0,"Profit_"+IntegerToString(i),OBJPROP_TEXT,(oc>0)?((prof>=0?"+":"")+DoubleToString(prof,2)):"--");
      ObjectSetInteger(0,"Profit_"+IntegerToString(i),OBJPROP_COLOR,(oc>0)?(prof>=0?clrLime:clrRed):clrGray);
      string ct="NO"; color cb=clrGray,ct2=clrBlack;
      if(oc>0){ct=(hB&&hS)?"ALL":hB?"BUY":"SEL";cb=(prof>=0)?clrLime:clrRed;ct2=(prof>=0)?clrBlack:clrWhite;}
      ObjectSetString(0,"BtnClose_"+IntegerToString(i),OBJPROP_TEXT,ct);
      ObjectSetInteger(0,"BtnClose_"+IntegerToString(i),OBJPROP_BGCOLOR,cb);
      ObjectSetInteger(0,"BtnClose_"+IntegerToString(i),OBJPROP_COLOR,ct2);
   }
   double tp=0; int to=0;
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber)continue;tp+=OrderProfit()+OrderSwap()+OrderCommission();to++;}
   ObjectSetString(0,"L_BalVal",OBJPROP_TEXT,"$"+DoubleToString(AccountBalance(),2));
   ObjectSetString(0,"L_MarginVal",OBJPROP_TEXT,"$"+DoubleToString(AccountFreeMargin(),2));
   string cat=(to>0)?((tp>=0?"+":"")+DoubleToString(tp,0)):"CLOSE";
   color cab=(to>0)?((tp>=0)?clrLime:clrRed):clrGray,catc=(to>0)?((tp>=0)?clrBlack:clrWhite):clrBlack;
   ObjectSetString(0,"HeaderCloseAll",OBJPROP_TEXT,cat+" ("+IntegerToString(to)+"/"+IntegerToString(runtimeMaxPos)+")");
   ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_BGCOLOR,cab);
   ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_COLOR,catc);
   UpdateAutoTradeBtn(); UpdateAlertBtn(); ChartRedraw();
}

// ===== HELPERS =====
void CreateLabel(string n,string t,int x,int y,color c,int s){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_LABEL,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetString(0,n,OBJPROP_TEXT,t);ObjectSetInteger(0,n,OBJPROP_COLOR,c);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,s);ObjectSetString(0,n,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);ObjectSetInteger(0,n,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
}
void CreateButton(string n,string t,int x,int y,int w,int h,color bg,color tc){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_BUTTON,0,0,0);
   ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x);ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w);ObjectSetInteger(0,n,OBJPROP_YSIZE,h);
   ObjectSetString(0,n,OBJPROP_TEXT,t);ObjectSetInteger(0,n,OBJPROP_COLOR,tc);
   ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg);ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,clrGray);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,runtimeFontSize);ObjectSetString(0,n,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false);ObjectSetInteger(0,n,OBJPROP_SELECTABLE,true);ObjectSetInteger(0,n,OBJPROP_SELECTED,false);
}
void DeleteAllObjects(){
   for(int i=ObjectsTotal(-1)-1;i>=0;i--){
      string n=ObjectName(i);
      if(StringFind(n,"RowBG_")==0||StringFind(n,"Pair_")==0||StringFind(n,"Profit_")==0||
         StringFind(n,"Signal_")==0||StringFind(n,"Score_")==0||StringFind(n,"Gap_")==0||
         StringFind(n,"Gates_")==0||StringFind(n,"RSI_")==0||
         StringFind(n,"Vol_")==0||StringFind(n,"Warn_")==0||
         StringFind(n,"BtnBuy_")==0||StringFind(n,"BtnSell_")==0||StringFind(n,"BtnClose_")==0||
         StringFind(n,"BtnAutoTrade")==0||StringFind(n,"BtnAlert")==0||
         StringFind(n,"BtnFont")==0||StringFind(n,"H_")==0||StringFind(n,"L_")==0||
         StringFind(n,"Header")==0||StringFind(n,"Max")==0||StringFind(n,"HDR_")==0) ObjectDelete(0,n);
   }
}
void UpdateMaxOrder(){ObjectSetString(0,"L_MaxVal",OBJPROP_TEXT,IntegerToString(runtimeMaxPos));}
void UpdateAutoTradeBtn(){
   ObjectSetString(0,"BtnAutoTrade",OBJPROP_TEXT,autoTradeON?"AUTO:ON":"AUTO:OFF");
   ObjectSetInteger(0,"BtnAutoTrade",OBJPROP_BGCOLOR,autoTradeON?clrDarkGreen:C'50,50,50');
   ObjectSetInteger(0,"BtnAutoTrade",OBJPROP_COLOR,autoTradeON?clrLime:clrGray);
}
void UpdateAlertBtn(){
   ObjectSetString(0,"BtnAlert",OBJPROP_TEXT,alertON?"ALERT:ON":"ALERT:OFF");
   ObjectSetInteger(0,"BtnAlert",OBJPROP_BGCOLOR,alertON?C'0,100,0':C'50,50,50');
   ObjectSetInteger(0,"BtnAlert",OBJPROP_COLOR,alertON?clrLime:clrGray);
}

// ===== TRAILING =====
void ManageTrailingStops(){
   for(int t=trailCount-1;t>=0;t--){bool f=false;for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderTicket()==trailData[t].ticket){f=true;break;}}if(!f){for(int k=t;k<trailCount-1;k++)trailData[k]=trailData[k+1];trailCount--;}}
   for(int j=0;j<OrdersTotal();j++){
      if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber)continue;if(OrderType()!=OP_BUY&&OrderType()!=OP_SELL)continue;
      int ti=-1; for(int t=0;t<trailCount;t++){if(trailData[t].ticket==OrderTicket()){ti=t;break;}}
      double atH=iATR(OrderSymbol(),PERIOD_H1,ATR_Period,0); if(atH<=0)continue;
      bool b=(OrderType()==OP_BUY); double cp=b?SymbolInfoDouble(OrderSymbol(),SYMBOL_BID):SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK);
      double op=OrderOpenPrice(),cs=OrderStopLoss(),pp=b?(cp-op):(op-cp); int dg=(int)MarketInfo(OrderSymbol(),MODE_DIGITS);
      if(ti<0){ti=trailCount;trailData[ti].ticket=OrderTicket();trailData[ti].peak=cp;trailData[ti].active=false;trailCount++;}
      if(b){if(cp>trailData[ti].peak)trailData[ti].peak=cp;}else{if(cp<trailData[ti].peak)trailData[ti].peak=cp;}
      if(!trailData[ti].active&&pp>=atH*1.0){trailData[ti].active=true;Print("Trail #",OrderTicket());}
      if(trailData[ti].active){
         double ns; int sl=(int)MarketInfo(OrderSymbol(),MODE_STOPLEVEL);
         if(b){ns=trailData[ti].peak-atH*0.8;if(ns>cs+atH*0.2||cs==0){ns=NormalizeDouble(ns,dg);double mn=cp-sl*SymbolInfoDouble(OrderSymbol(),SYMBOL_POINT);if(ns<mn)ns=mn;OrderModify(OrderTicket(),op,ns,OrderTakeProfit(),0,clrWhite);}}
         else{ns=trailData[ti].peak+atH*0.8;if(ns<cs-atH*0.2||cs==0){ns=NormalizeDouble(ns,dg);double mx=cp+sl*SymbolInfoDouble(OrderSymbol(),SYMBOL_POINT);if(ns>mx)ns=mx;OrderModify(OrderTicket(),op,ns,OrderTakeProfit(),0,clrWhite);}}
      }
   }
}

// ===== TRADING =====
void OpenTrade(string sym,int type){
   if(!IsTradeAllowed()){Print("Trading not allowed");return;}
   if(!SymbolSelect(sym,true)){Print("Symbol not found: ",sym);return;}
   int pc=0; for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()==MagicNumber&&(OrderType()==OP_BUY||OrderType()==OP_SELL))pc++;}
   if(pc>=runtimeMaxPos){Print("Max positions");return;}
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()==sym&&OrderMagicNumber()==MagicNumber&&OrderType()==type){Print("Already have ",(type==OP_BUY?"BUY":"SELL"));return;}}
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK),bid=SymbolInfoDouble(sym,SYMBOL_BID); if(ask<=0||bid<=0){Print("Invalid price");return;}
   double lot=NormalizeDouble(LotSize,2);
   double minL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MIN),maxL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MAX);
   if(lot<minL)lot=minL;if(lot>maxL)lot=maxL;
   double at=iATR(sym,PERIOD_H1,ATR_Period,0),p=(type==OP_BUY)?ask:bid,sl=0,tp=0;
   if(at>0){sl=(type==OP_BUY)?p-at*ATR_SL_Mult:p+at*ATR_SL_Mult;tp=(type==OP_BUY)?p+at*ATR_TP_Mult:p-at*ATR_TP_Mult;int d=(int)MarketInfo(sym,MODE_DIGITS);sl=NormalizeDouble(sl,d);tp=NormalizeDouble(tp,d);}
   int t=OrderSend(sym,type,lot,p,Slippage,sl,tp,"CCS Dash",MagicNumber,0,clrNONE);
   if(t>0)Print("Order #",t," ",(type==OP_BUY?"BUY":"SELL")," ",sym," Lot:",lot);
   else{
      Print("OrderSend failed err:",GetLastError()," retry no SL/TP");
      t=OrderSend(sym,type,lot,p,Slippage,0,0,"CCS Dash",MagicNumber,0,clrNONE);
      if(t>0&&at>0&&OrderSelect(t,SELECT_BY_TICKET)){int d2=(int)MarketInfo(sym,MODE_DIGITS);sl=(type==OP_BUY)?OrderOpenPrice()-at*ATR_SL_Mult:OrderOpenPrice()+at*ATR_SL_Mult;tp=(type==OP_BUY)?OrderOpenPrice()+at*ATR_TP_Mult:OrderOpenPrice()-at*ATR_TP_Mult;OrderModify(t,OrderOpenPrice(),NormalizeDouble(sl,d2),NormalizeDouble(tp,d2),0,clrNONE);}
   }
}
void CloseSymbol(string sym){
   for(int i=OrdersTotal()-1;i>=0;i--){if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=sym||OrderMagicNumber()!=MagicNumber)continue;double cp;color ac;if(OrderType()==OP_BUY){cp=SymbolInfoDouble(sym,SYMBOL_BID);ac=clrRed;}else{cp=SymbolInfoDouble(sym,SYMBOL_ASK);ac=clrBlue;}if(OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac)){for(int t=trailCount-1;t>=0;t--){if(trailData[t].ticket==OrderTicket()){for(int k=t;k<trailCount-1;k++)trailData[k]=trailData[k+1];trailCount--;break;}}}else Print("Close fail #",OrderTicket()," err:",GetLastError());}
}
void CloseAllPositions(){
   for(int i=OrdersTotal()-1;i>=0;i--){if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber)continue;double cp;color ac;if(OrderType()==OP_BUY){cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_BID);ac=clrRed;}else{cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK);ac=clrBlue;}OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac);}
}
void RunAutoTrade(){
   for(int i=0;i<totalPairs;i++){if(ccsData[i].signal!=2&&ccsData[i].signal!=-2)continue;
      int dt=(ccsData[i].signal==2)?OP_BUY:OP_SELL,ot=(ccsData[i].signal==2)?OP_SELL:OP_BUY;
      bool hD=false,hO=false;
      for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=pairs[i]||OrderMagicNumber()!=MagicNumber)continue;if(OrderType()==dt)hD=true;if(OrderType()==ot)hO=true;}
      if(hO){CloseSymbol(pairs[i]);Sleep(200);}if(hD)continue;
      int tt=0;for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()==MagicNumber&&(OrderType()==OP_BUY||OrderType()==OP_SELL))tt++;}
      if(tt>=runtimeMaxPos)break;OpenTrade(pairs[i],dt);
   }
}
void CheckAlerts(){
   for(int i=0;i<totalPairs;i++){int s=ccsData[i].signal;if(s!=2&&s!=-2)continue;
      string d=(s==2)?"STRONG BUY":"STRONG SELL";
      if(lastAlertSignal[i]==d&&TimeCurrent()-lastAlertTime[i]<600)continue;lastAlertSignal[i]=d;lastAlertTime[i]=TimeCurrent();
      string w=(StringLen(ccsData[i].warning)>0)?" ["+ccsData[i].warning+"]":"";
      string m="CCS: "+d+" "+pairs[i]+" GAP:"+DoubleToString(MathAbs(ccsData[i].ccyGap),1)+" GT:"+IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear)+" RSI:"+DoubleToString(ccsData[i].rsi,1)+" S:"+IntegerToString(MathAbs(ccsData[i].score))+"/10"+w;
      if(alertON){Alert(m);SendNotification(m);}Print(m);
   }
}
//+------------------------------------------------------------------+
