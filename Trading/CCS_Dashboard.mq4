//+------------------------------------------------------------------+
//|                                            CCS_Dashboard.mq4 v1.05|
//|          Callunk Confluence System — 29 Pair EA + ALL Indicators |
//+------------------------------------------------------------------+
#property copyright "Callunk & Cuy"
#property version   "1.05"
#property strict
#property description "CCS Dashboard — 29 Pair | Kolom RSI/SnR/ATR/BB semua ON"
#property description "Klik header utk toggle | GAP + GT + RSI + SnR + ATR + BB"

input int    FontSize     =  8;  input color TextColor=clrWhite; input color HeaderColor=clrYellow;
input int    StartX=10, StartY=25;
input string CustomPairs="AUDCAD,AUDCHF,AUDJPY,AUDNZD,AUDUSD,CADCHF,CADJPY,CHFJPY,EURAUD,EURCAD,EURCHF,EURGBP,EURJPY,EURNZD,EURUSD,GBPAUD,GBPCAD,GBPCHF,GBPJPY,GBPNZD,GBPUSD,NZDCAD,NZDCHF,NZDJPY,NZDUSD,USDCAD,USDCHF,USDJPY";
input double LotSize=0.01; input int MagicNumber=20260506, MaxOpenPositions=3, Slippage=10;
input double ATR_SL_Mult=1.5, ATR_TP_Mult=2.0;
input int BB_Period=20; input double BB_Deviation=2.0;
input int RSI_Period=14; input double RSI_Oversold=30.0, RSI_Overbought=70.0;
input int ATR_Period=14, SnR_BarsLeft=3, SnR_BarsRight=3, SnR_MaxLevels=20;
input int EMA20_Period=20, EMA50_Period=50, EMA100_Period=100, EMA200_Period=200;
input double CS_Strong_Threshold=5.0;

string pairs[]; int totalPairs; bool autoTradeON=false, alertON=true;
int runtimeMaxPos=0, runtimeFontSize=8; datetime lastUpdateTime=0; int updateCounter=0;
struct CCSData{string pair;int signal,prevSignal,gateBull,gateBear,score;double rsi,atr,ccyGap,snrDist;bool bbTouchLow,bbTouchHigh,atrNaik;string regime,warning;};
CCSData ccsData[]; string lastAlertSignal[]; datetime lastAlertTime[];
bool tog_RSI=true, tog_VOL=true, tog_SnR=true, tog_BB=true, tog_WARN=true;
struct TrailData{int ticket;double peak;bool active;}; TrailData trailData[]; int trailCount=0;
string ccyList[8]={"USD","EUR","GBP","CHF","CAD","AUD","JPY","NZD"};
int cci(string c){for(int i=0;i<8;i++)if(ccyList[i]==c)return i;return -1;}
color RGB(int r,int g,int b){return(color)((r&0xFF)|((g&0xFF)<<8)|((b&0xFF)<<16));}

int OnInit(){
   runtimeMaxPos=MaxOpenPositions; runtimeFontSize=FontSize;
   string s=CustomPairs; totalPairs=1;
   for(int i=0;i<StringLen(s);i++)if(StringGetCharacter(s,i)==',')totalPairs++;
   ArrayResize(pairs,totalPairs); int start=0,idx=0;
   for(int i=0;i<=StringLen(s);i++){if(i==StringLen(s)||StringGetCharacter(s,i)==','){if(i>start){string p=StringSubstr(s,start,i-start);if(StringLen(p)>0)pairs[idx++]=p;}start=i+1;}}
   totalPairs=idx; ArrayResize(pairs,totalPairs);
   ArrayResize(ccsData,totalPairs); ArrayResize(lastAlertSignal,totalPairs); ArrayResize(lastAlertTime,totalPairs);
   for(int i=0;i<totalPairs;i++){ccsData[i].prevSignal=0;lastAlertSignal[i]="";lastAlertTime[i]=0;}
   ArrayResize(trailData,50); trailCount=0; CreateDashboard(); EventSetTimer(1); return INIT_SUCCEEDED;
}
void OnDeinit(const int r){EventKillTimer();DeleteAllObjects();}
void OnTick(){datetime n=TimeCurrent();if(n==lastUpdateTime)return;lastUpdateTime=n;updateCounter++;UpdateAllSignals();if(updateCounter%2==0&&autoTradeON)RunAutoTrade();ManageTrailingStops();UpdateDashboard();}
void OnTimer(){datetime n=TimeCurrent();if(n==lastUpdateTime)return;lastUpdateTime=n;updateCounter++;UpdateAllSignals();if(updateCounter%2==0){CheckAlerts();if(autoTradeON)RunAutoTrade();}ManageTrailingStops();UpdateDashboard();}
void OnChartEvent(const int id,const long&lparam,const double&dparam,const string&sparam){
   if(id!=CHARTEVENT_OBJECT_CLICK)return;
   if(sparam=="AUTO"){autoTradeON=!autoTradeON;ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="ALERT"){alertON=!alertON;ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HeaderCloseAll"){CloseAllPositions();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="F-"){ResizeFont(runtimeFontSize-1);ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="F+"){ResizeFont(runtimeFontSize+1);ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_RSI"){tog_RSI=!tog_RSI;UpdateHD();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_SnR"){tog_SnR=!tog_SnR;UpdateHD();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_ATR"){tog_VOL=!tog_VOL;UpdateHD();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_BB"){tog_BB=!tog_BB;UpdateHD();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="HDR_WARN"){tog_WARN=!tog_WARN;UpdateHD();ChartRedraw();ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"BK_")==0){int i=(int)StringToInteger(StringSubstr(sparam,3));if(i>=0&&i<totalPairs){OpenTrade(pairs[i],OP_BUY);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"BS_")==0){int i=(int)StringToInteger(StringSubstr(sparam,3));if(i>=0&&i<totalPairs){OpenTrade(pairs[i],OP_SELL);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(StringFind(sparam,"BX_")==0){int i=(int)StringToInteger(StringSubstr(sparam,3));if(i>=0&&i<totalPairs){CloseSymbol(pairs[i]);ChartRedraw();}ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="M1"){if(runtimeMaxPos>1)runtimeMaxPos--;ObjectSetString(0,"L1",OBJPROP_TEXT,IntegerToString(runtimeMaxPos));ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
   if(sparam=="M2"){if(runtimeMaxPos<10)runtimeMaxPos++;ObjectSetString(0,"L1",OBJPROP_TEXT,IntegerToString(runtimeMaxPos));ObjectSetInteger(0,sparam,OBJPROP_SELECTED,false);return;}
}
void ResizeFont(int n){if(n<6||n>22)return;runtimeFontSize=n;DeleteAllObjects();CreateDashboard();ChartRedraw();}
void UpdateHD(){
   ObjectSetInteger(0,"HDR_RSI",OBJPROP_COLOR,tog_RSI?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_SnR",OBJPROP_COLOR,tog_SnR?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_ATR",OBJPROP_COLOR,tog_VOL?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_BB", OBJPROP_COLOR,tog_BB?clrYellow:clrDimGray);
   ObjectSetInteger(0,"HDR_WARN",OBJPROP_COLOR,tog_WARN?clrYellow:clrDimGray);
}

// ===== SIGNALS =====
void UpdateAllSignals(){
   CalcCS(); for(int i=0;i<totalPairs;i++){int r=CalcSig(pairs[i],i);int pv=ccsData[i].prevSignal;int o=r;
      if(pv>=2&&r<=-1)o=0;if(pv<=-2&&r>=1)o=0;if(pv>=1&&r<=-2)o=0;if(pv<=-1&&r>=2)o=0;if(pv==2&&r==0)o=1;if(pv==-2&&r==0)o=-1;ccsData[i].prevSignal=o;ccsData[i].signal=o;}
}
double ccyStrength[8]={0,0,0,0,0,0,0,0};
void CalcCS(){
   double s[28]; string p[28]={"GBPUSD","USDCHF","EURUSD","USDJPY","USDCAD","NZDUSD","AUDUSD","AUDNZD","AUDCAD","AUDCHF","AUDJPY","CADJPY","CHFJPY","EURGBP","EURAUD","EURCHF","EURJPY","EURNZD","EURCAD","GBPCHF","GBPAUD","GBPCAD","GBPJPY","GBPNZD","NZDJPY","NZDCAD","CHFCAD","NZDCHF"};
   for(int i=0;i<28;i++){double dc=iClose(p[i],PERIOD_D1,0),dh=iHigh(p[i],PERIOD_D1,0),dl=iLow(p[i],PERIOD_D1,0);if(dh<=dl||dc<=0){s[i]=-1;continue;}double r=(dc-dl)/(dh-dl);if(r>=0.97)s[i]=9;else if(r>=0.90)s[i]=8;else if(r>=0.75)s[i]=7;else if(r>=0.60)s[i]=6;else if(r>=0.50)s[i]=5;else if(r>=0.40)s[i]=4;else if(r>=0.25)s[i]=3;else if(r>=0.10)s[i]=2;else if(r>=0.03)s[i]=1;else s[i]=0;}
   double su[8]; su[0]=((9-s[0])+s[1]+(9-s[2])+s[3]+s[4]+(9-s[5])+(9-s[6]))/7.0; su[1]=(s[2]+s[13]+s[14]+s[15]+s[16]+s[17]+s[18])/7.0;
   su[2]=(s[0]+(9-s[13])+s[19]+s[20]+s[21]+s[22]+s[23])/7.0; su[3]=((9-s[1])+(9-s[9])+s[12]+(9-s[15])+(9-s[19])+s[26]+(9-s[27]))/7.0;
   su[4]=((9-s[4])+(9-s[8])+s[11]+(9-s[18])+(9-s[21])+(9-s[25])+(9-s[26]))/7.0; su[5]=(s[6]+s[7]+s[8]+s[9]+s[10]+(9-s[14])+(9-s[20]))/7.0;
   su[6]=((9-s[3])+(9-s[10])+(9-s[11])+(9-s[12])+(9-s[16])+(9-s[22])+(9-s[24]))/7.0; su[7]=(s[5]+(9-s[7])+(9-s[17])+(9-s[23])+s[24]+s[25]+s[27])/7.0;
   for(int i=0;i<8;i++)ccyStrength[i]=su[i];
}
double GetGap(string sym){
   string b="",q="";if(sym=="XAUUSD"){b="XAU";q="USD";}else if(StringLen(sym)==6){b=StringSubstr(sym,0,3);q=StringSubstr(sym,3,3);}else return 0;
   int bi=cci(b),qi=cci(q);if(bi<0||qi<0)return 0;return NormalizeDouble(ccyStrength[bi]-ccyStrength[qi],1);
}

int CalcSig(string sym,int idx){
   if(MarketInfo(sym,MODE_BID)<=0)return 0;
   double c=iClose(sym,PERIOD_H1,0),e20=iMA(sym,PERIOD_H1,20,0,MODE_EMA,PRICE_CLOSE,0);
   double e50=iMA(sym,PERIOD_H1,50,0,MODE_EMA,PRICE_CLOSE,0),e100=iMA(sym,PERIOD_H1,100,0,MODE_EMA,PRICE_CLOSE,0);
   double e200=iMA(sym,PERIOD_H1,200,0,MODE_EMA,PRICE_CLOSE,0);
   double bl=iBands(sym,PERIOD_H1,BB_Period,BB_Deviation,0,PRICE_CLOSE,MODE_LOWER,0);
   double bu=iBands(sym,PERIOD_H1,BB_Period,BB_Deviation,0,PRICE_CLOSE,MODE_UPPER,0);
   double r=iRSI(sym,PERIOD_H1,RSI_Period,PRICE_CLOSE,0),rp=iRSI(sym,PERIOD_H1,RSI_Period,PRICE_CLOSE,1);
   double at=iATR(sym,PERIOD_H1,ATR_Period,0),atp=iATR(sym,PERIOD_H1,ATR_Period,10);
   double hh=iHigh(sym,PERIOD_H1,0),ll=iLow(sym,PERIOD_H1,0);
   ccsData[idx].ccyGap=GetGap(sym); ccsData[idx].rsi=r; ccsData[idx].atr=at;
   ccsData[idx].bbTouchLow=(bl>0&&ll<=bl); ccsData[idx].bbTouchHigh=(bu>0&&hh>=bu);
   if(c==0||r==0)return 0;
   int gb=0,gs=0; if(e20>0&&c>e20)gb++;else if(e20>0&&c<e20)gs++;
   if(e50>0&&c>e50)gb++;else if(e50>0&&c<e50)gs++;if(e100>0&&c>e100)gb++;else if(e100>0&&c<e100)gs++;
   if(e200>0&&c>e200)gb++;else if(e200>0&&c<e200)gs++;ccsData[idx].gateBull=gb;ccsData[idx].gateBear=gs;
   double ns=0,nr=0,nsD=999999,nrD=999999; ccsData[idx].snrDist=999; int bars=MathMin(200,iBars(sym,PERIOD_H1));
   if(bars>=SnR_BarsLeft+SnR_BarsRight+1){
      for(int b=SnR_BarsLeft;b<bars-SnR_BarsRight;b++){double sh=iHigh(sym,PERIOD_H1,b),sl=iLow(sym,PERIOD_H1,b);bool isSH=true,isSL=true;
         for(int j=1;j<=SnR_BarsLeft;j++){if(sh<=iHigh(sym,PERIOD_H1,b+j))isSH=false;if(sl>=iLow(sym,PERIOD_H1,b+j))isSL=false;}
         for(int j=1;j<=SnR_BarsRight;j++){if(sh<=iHigh(sym,PERIOD_H1,b-j))isSH=false;if(sl>=iLow(sym,PERIOD_H1,b-j))isSL=false;}
         if(isSH==isSL)continue;if(isSH){double d2=MathAbs(sh-c);if(c<sh&&d2<nrD){nr=sh;nrD=d2;}}if(isSL){double d3=MathAbs(sl-c);if(c>sl&&d3<nsD){ns=sl;nsD=d3;}}}
   }
   double aS=(at>0)?at:1; bool nS=(ns>0&&nsD<aS*1.5),nR=(nr>0&&nrD<aS*1.5);
   if(nS)ccsData[idx].snrDist=nsD/aS; if(nR)ccsData[idx].snrDist=nrD/aS;
   bool rOs=(r>0&&r<RSI_Oversold),rOb=(r>RSI_Overbought),rTu=(r>rp&&rp<RSI_Oversold),rTd=(r<rp&&rp>RSI_Overbought);
   bool pv=(atp>0),aN=(pv&&at>atp),aT=(pv&&at<atp); ccsData[idx].atrNaik=aN;
   string vt="=Nor"; if(aT)vt="Sta";else if(aN)vt="Vol"; ccsData[idx].regime=vt;
   double gap=ccsData[idx].ccyGap; bool gBull=(gap>0.5),gBear=(gap<-0.5);
   int bs=0,ss=0;
   if(gBull){
      // GAP kontribusi: 5.0→+2, 6.0→+3, 7.0→+4, 8.0→+5, 9.0→+6
      bs+=MathMax(0,(int)(gap-3));
      if(gb>=4)bs+=3;else if(gb>=3)bs+=2;else if(gb>=2)bs+=1;
      if(tog_RSI){
         if(rOs)bs+=1;             // RSI oversold = konfirmasi
         else if(rOb)bs-=1;        // RSI overbought = kontradiksi
         else if(rTu)bs+=1;        // RSI turning up = momentum
      }
      if(tog_BB){
         if(ccsData[idx].bbTouchLow)bs+=1;
         else if(ccsData[idx].bbTouchHigh)bs-=1; // kontradiksi
      }
      if(tog_VOL){if(aT)bs+=1;else if(aN)bs-=1;}
      if(tog_SnR){if(nS)bs+=1;else if(nR)bs-=1;} // kontradiksi: dekat resist
      if(gs>gb)bs-=2;
   }else if(gBear){
      ss+=MathMax(0,(int)(MathAbs(gap)-3));
      if(gs>=4)ss+=3;else if(gs>=3)ss+=2;else if(gs>=2)ss+=1;
      if(tog_RSI){
         if(rOb)ss+=1;             // RSI overbought = konfirmasi
         else if(rOs)ss-=1;        // RSI oversold = kontradiksi
         else if(rTd)ss+=1;        // RSI turning down = momentum
      }
      if(tog_BB){
         if(ccsData[idx].bbTouchHigh)ss+=1;
         else if(ccsData[idx].bbTouchLow)ss-=1; // kontradiksi
      }
      if(tog_VOL){if(aT)ss+=1;else if(aN)ss-=1;}
      if(tog_SnR){if(nR)ss+=1;else if(nS)ss-=1;} // kontradiksi: dekat support
      if(gb>gs)ss-=2;
   }else{ccsData[idx].warning="";ccsData[idx].score=0;return 0;}
   string w="";if(aN&&r>70)w="VolTop";else if(aN&&r<30)w="VolBot";else if(ccsData[idx].bbTouchHigh&&rOb)w="OB+BB";else if(ccsData[idx].bbTouchLow&&rOs)w="OS+BB";
   else if(nR&&gb>=3)w="~Res";else if(nS&&gs>=3)w="~Sup";else if(atp>0&&at>atp*1.5)w="ATR+";ccsData[idx].warning=w;
   // Warning penalty (hanya jika toggle WARN ON)
   if(tog_WARN){
      if(w=="VolTop"||w=="OB+BB")bs-=2;
      else if(w=="VolBot"||w=="OS+BB")ss-=2;
      else if(w=="~Res")bs-=1;
      else if(w=="~Sup")ss-=1;
      else if(w=="ATR+"){bs-=1;ss-=1;}
   }
   ccsData[idx].score=(bs>ss)?bs:(ss>bs)?-ss:0;
   if(bs>=7)return 2;if(bs>=4)return 1;if(ss>=7)return -2;if(ss>=4)return -1;return 0;
}

// ===== DASHBOARD =====
void CreateDashboard(){
   int x=StartX,y=StartY,fs=runtimeFontSize,useLH=(int)(fs*1.8+1); double cs=(double)fs/8.0; if(cs<1.0)cs=1.0;
   // Column layout: PAIR | PL | SIG | % | GAP | GT | RSI | SnR | ATR | BB | WARN | B | S | X
   int c0=x, c1=c0+(int)(45*cs), c2=c1+(int)(50*cs), c3=c2+(int)(55*cs), cPct=c3+(int)(28*cs);
   int c4=cPct+(int)(28*cs), c5=c4+(int)(45*cs), c6=c5+(int)(45*cs);
   int cSnR=c6+(int)(45*cs), cATR=cSnR+(int)(40*cs), cBB=cATR+(int)(35*cs);
   int cWarn=cBB+(int)(35*cs);
   int cB=cWarn+(int)(50*cs), cS=cB+(int)(28*cs), cX=cS+(int)(28*cs);
   int totalW=cX+(int)(40*cs), btnH=useLH-2; if(btnH<12)btnH=12;
   // Headers
   int hy=y; CreateLabel("H_Pair","PR",c0,hy,HeaderColor,fs); CreateLabel("H_Profit","PL",c1,hy,HeaderColor,fs);
   CreateLabel("H_Signal","SIG",c2,hy,HeaderColor,fs); CreateLabel("H_Pct","%",cPct,hy,clrDodgerBlue,fs);
   CreateLabel("H_Gap","GAP",c4,hy,HeaderColor,fs); CreateLabel("H_Gates","GT",c5,hy,HeaderColor,fs);
   HDR("HDR_RSI","RSI",c6,hy,(int)(45*cs),useLH,fs); HDR("HDR_SnR","SnR",cSnR,hy,(int)(40*cs),useLH,fs);
   HDR("HDR_ATR","ATR",cATR,hy,(int)(35*cs),useLH,fs); HDR("HDR_BB","BB",cBB,hy,(int)(35*cs),useLH,fs);
   HDR("HDR_WARN","WN",cWarn,hy,(int)(40*cs),useLH,fs);
   CreateButton("HeaderCloseAll","X",cB,hy-2,(int)(80*cs),18,clrGray,clrBlack);
   y+=useLH+5;
   for(int i=0;i<totalPairs;i++){
      int ry=y+i*useLH,ly=ry+1;
      ObjectCreate(0,"RBG_"+IntegerToString(i),OBJ_RECTANGLE_LABEL,0,0,0); ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_XDISTANCE,x);
      ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_YDISTANCE,ry); ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_XSIZE,totalW);
      ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_YSIZE,useLH-1); ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_BGCOLOR,RGB(35,35,35)); ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_BORDER_COLOR,RGB(50,50,50));
      ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_BACK,true); ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,"RBG_"+IntegerToString(i),OBJPROP_HIDDEN,true);
      CreateLabel("PR_"+IntegerToString(i),pairs[i],c0,ly,TextColor,fs); CreateLabel("PL_"+IntegerToString(i),"--",c1,ly,clrGray,fs);
      CreateLabel("SG_"+IntegerToString(i),"WAIT",c2,ly,clrGray,fs); CreateLabel("PC_"+IntegerToString(i),"",cPct,ly,clrGray,fs);
      CreateLabel("GP_"+IntegerToString(i),"--",c4,ly,clrGray,fs); CreateLabel("GT_"+IntegerToString(i),"--",c5,ly,clrGray,fs);
      CreateLabel("RS_"+IntegerToString(i),"--",c6,ly,clrGray,fs); CreateLabel("SR_"+IntegerToString(i),"--",cSnR,ly,clrGray,fs);
      CreateLabel("AV_"+IntegerToString(i),"--",cATR,ly,clrGray,fs); CreateLabel("BB_"+IntegerToString(i),"--",cBB,ly,clrGray,fs);
      CreateLabel("WN_"+IntegerToString(i),"",cWarn,ly,clrGray,fs);
      CreateButton("BK_"+IntegerToString(i),"B",cB,ry+1,(int)(28*cs),btnH,clrForestGreen,clrWhite);
      CreateButton("BS_"+IntegerToString(i),"S",cS,ry+1,(int)(28*cs),btnH,clrCrimson,clrWhite);
      CreateButton("BX_"+IntegerToString(i),"NO",cX,ry+1,(int)(35*cs),btnH,clrGray,clrBlack);
   }
   // Bottom
   int bY=y+(totalPairs+1)*useLH; int b=x;
   CreateLabel("L0","MAX:",b,bY,HeaderColor,fs); b+=(int)(30*cs); CreateButton("M1","-",b,bY-2,(int)(16*cs),(int)(14*cs),clrRed,clrWhite); b+=(int)(18*cs);
   CreateLabel("L1",IntegerToString(runtimeMaxPos),b,bY,clrLime,fs); b+=(int)(20*cs); CreateButton("M2","+",b,bY-2,(int)(16*cs),(int)(14*cs),clrLime,clrBlack);
   b+=(int)(30*cs); CreateLabel("L2","BAL:",b,bY,HeaderColor,fs); b+=(int)(30*cs); CreateLabel("L3","$0",b,bY,clrLime,fs); b+=(int)(50*cs);
   CreateLabel("L4","MAR:",b,bY,HeaderColor,fs); b+=(int)(30*cs); CreateLabel("L5","$0",b,bY,clrLime,fs); b+=(int)(50*cs);
   CreateButton("F-","F-",b,bY-2,(int)(20*cs),(int)(14*cs),clrGray,clrWhite); b+=(int)(25*cs); CreateLabel("L6","F"+IntegerToString(runtimeFontSize),b,bY,clrLightGray,fs); b+=(int)(25*cs);
   CreateButton("F+","F+",b,bY-2,(int)(20*cs),(int)(14*cs),clrLime,clrBlack); b+=(int)(30*cs);
   CreateButton("AUTO","AUTO",b,bY-2,(int)(65*cs),(int)(14*cs),C'50,50,50',clrGray); b+=(int)(70*cs);
   CreateButton("ALERT","ALERT",b,bY-2,(int)(65*cs),(int)(14*cs),C'0,100,0',clrLime);
}
void HDR(string n,string t,int x,int y,int w,int h,int fs){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_BUTTON,0,0,0); ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x); ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w); ObjectSetInteger(0,n,OBJPROP_YSIZE,h); ObjectSetString(0,n,OBJPROP_TEXT,t);
   ObjectSetInteger(0,n,OBJPROP_COLOR,clrYellow); ObjectSetInteger(0,n,OBJPROP_BGCOLOR,clrBlack); ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,clrBlack);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,fs); ObjectSetString(0,n,OBJPROP_FONT,"Consolas"); ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,n,OBJPROP_BACK,false); ObjectSetInteger(0,n,OBJPROP_SELECTABLE,true); ObjectSetInteger(0,n,OBJPROP_SELECTED,false);
}

void UpdateDashboard(){
   for(int i=0;i<totalPairs;i++){
      int sg=ccsData[i].signal; string st="Wait"; color sc=clrGray;
      if(sg==2){st="StrB";sc=clrLime;}else if(sg==1){st="Buy";sc=clrMediumSeaGreen;}else if(sg==-1){st="Sell";sc=clrTomato;}else if(sg==-2){st="StrS";sc=clrRed;}
      ObjectSetString(0,"SG_"+IntegerToString(i),OBJPROP_TEXT,st); ObjectSetInteger(0,"SG_"+IntegerToString(i),OBJPROP_COLOR,sc);
      // Score %
      int rs=ccsData[i].score; int dynMax=9+(tog_RSI?1:0)+(tog_SnR?1:0)+(tog_VOL?1:0)+(tog_BB?1:0)+(tog_WARN?0:0); int pct=(dynMax>0)?(int)(MathAbs(rs)*100/dynMax):0; if(pct>100)pct=100;
      color pc2=clrGray; if(rs>=7)pc2=clrLime;else if(rs>=4)pc2=clrMediumSeaGreen;else if(rs<=-7)pc2=clrRed;else if(rs<=-4)pc2=clrTomato;
      ObjectSetString(0,"PC_"+IntegerToString(i),OBJPROP_TEXT,(pct>0)?(IntegerToString(pct)+"%"):""); ObjectSetInteger(0,"PC_"+IntegerToString(i),OBJPROP_COLOR,pc2);
      // GAP
      double gv=ccsData[i].ccyGap; color goc=(gv>=CS_Strong_Threshold)?clrLime:(gv<=-CS_Strong_Threshold)?clrRed:clrGray;
      ObjectSetString(0,"GP_"+IntegerToString(i),OBJPROP_TEXT,DoubleToString(MathAbs(gv),1)); ObjectSetInteger(0,"GP_"+IntegerToString(i),OBJPROP_COLOR,goc);
      // GT
      ObjectSetString(0,"GT_"+IntegerToString(i),OBJPROP_TEXT,IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear));
      ObjectSetInteger(0,"GT_"+IntegerToString(i),OBJPROP_COLOR,(ccsData[i].gateBull>ccsData[i].gateBear)?clrMediumSeaGreen:(ccsData[i].gateBear>ccsData[i].gateBull)?clrTomato:clrGray);
      // RSI
      double rv=ccsData[i].rsi; ObjectSetString(0,"RS_"+IntegerToString(i),OBJPROP_TEXT,DoubleToString(rv,1));
      ObjectSetInteger(0,"RS_"+IntegerToString(i),OBJPROP_COLOR,tog_RSI?((rv>0&&rv<RSI_Oversold)?clrLime:(rv>RSI_Overbought)?clrRed:clrWhite):clrGray);
      // SnR -- show distance to nearest S/R in ATR
      double sd=ccsData[i].snrDist; string srT=(sd>0&&sd<999)?DoubleToString(sd,1):"-";
      ObjectSetString(0,"SR_"+IntegerToString(i),OBJPROP_TEXT,srT);
      ObjectSetInteger(0,"SR_"+IntegerToString(i),OBJPROP_COLOR,tog_SnR?((sd>0&&sd<1.5)?clrMediumSeaGreen:clrWhite):clrGray);
      // ATR
      double av=ccsData[i].atr; string avT=(av>0)?(DoubleToString(av,1)+(ccsData[i].atrNaik?"^":"v")):"-";
      ObjectSetString(0,"AV_"+IntegerToString(i),OBJPROP_TEXT,avT);
      ObjectSetInteger(0,"AV_"+IntegerToString(i),OBJPROP_COLOR,tog_VOL?((av>0)?(ccsData[i].atrNaik?clrOrange:clrWhite):clrGray):clrGray);
      // BB
      string bt="M"; color bc2=clrGray; if(ccsData[i].bbTouchLow){bt="L";bc2=clrLime;}else if(ccsData[i].bbTouchHigh){bt="H";bc2=clrRed;}
      ObjectSetString(0,"BB_"+IntegerToString(i),OBJPROP_TEXT,bt); ObjectSetInteger(0,"BB_"+IntegerToString(i),OBJPROP_COLOR,tog_BB?bc2:clrGray);
      // WARN
      ObjectSetString(0,"WN_"+IntegerToString(i),OBJPROP_TEXT,ccsData[i].warning); color wc2=clrGray;
      if(StringFind(ccsData[i].warning,"Vol")==0||StringFind(ccsData[i].warning,"OB+")==0||StringFind(ccsData[i].warning,"OS+")==0)wc2=clrRed;
      else if(StringLen(ccsData[i].warning)>0)wc2=clrOrange; ObjectSetInteger(0,"WN_"+IntegerToString(i),OBJPROP_COLOR,wc2);
      // PROFIT + CLOSE
      double prof=0; int oc=0; bool hB=false,hS=false;
      for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=pairs[i]||OrderMagicNumber()!=MagicNumber)continue;prof+=OrderProfit()+OrderSwap()+OrderCommission();oc++;if(OrderType()==OP_BUY)hB=true;if(OrderType()==OP_SELL)hS=true;}
      ObjectSetString(0,"PL_"+IntegerToString(i),OBJPROP_TEXT,(oc>0)?((prof>=0?"+":"")+DoubleToString(prof,2)):"--");
      ObjectSetInteger(0,"PL_"+IntegerToString(i),OBJPROP_COLOR,(oc>0)?(prof>=0?clrLime:clrRed):clrGray);
      string ct="NO"; color cb=clrGray,ct2=clrBlack; if(oc>0){ct=(hB&&hS)?"A":hB?"B":"S";cb=(prof>=0)?clrLime:clrRed;ct2=(prof>=0)?clrBlack:clrWhite;}
      ObjectSetString(0,"BX_"+IntegerToString(i),OBJPROP_TEXT,ct); ObjectSetInteger(0,"BX_"+IntegerToString(i),OBJPROP_BGCOLOR,cb); ObjectSetInteger(0,"BX_"+IntegerToString(i),OBJPROP_COLOR,ct2);
   }
   double tp=0; int to=0;
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber)continue;tp+=OrderProfit()+OrderSwap()+OrderCommission();to++;}
   ObjectSetString(0,"L3",OBJPROP_TEXT,"$"+DoubleToString(AccountBalance(),2)); ObjectSetString(0,"L5",OBJPROP_TEXT,"$"+DoubleToString(AccountFreeMargin(),2));
   string cat=(to>0)?((tp>=0?"+":"")+DoubleToString(tp,0)):"X"; color cab=(to>0)?((tp>=0)?clrLime:clrRed):clrGray,catc=(to>0)?((tp>=0)?clrBlack:clrWhite):clrBlack;
   ObjectSetString(0,"HeaderCloseAll",OBJPROP_TEXT,cat+"("+IntegerToString(to)+"/"+IntegerToString(runtimeMaxPos)+")");
   ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_BGCOLOR,cab); ObjectSetInteger(0,"HeaderCloseAll",OBJPROP_COLOR,catc);
   // Auto/Alert buttons
   ObjectSetString(0,"AUTO",OBJPROP_TEXT,autoTradeON?"A:ON":"A:OF"); ObjectSetInteger(0,"AUTO",OBJPROP_BGCOLOR,autoTradeON?clrDarkGreen:C'50,50,50'); ObjectSetInteger(0,"AUTO",OBJPROP_COLOR,autoTradeON?clrLime:clrGray);
   ObjectSetString(0,"ALERT",OBJPROP_TEXT,alertON?"AL:ON":"AL:OF"); ObjectSetInteger(0,"ALERT",OBJPROP_BGCOLOR,alertON?C'0,100,0':C'50,50,50'); ObjectSetInteger(0,"ALERT",OBJPROP_COLOR,alertON?clrLime:clrGray);
   ChartRedraw();
}
void CreateLabel(string n,string t,int x,int y,color c,int s){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_LABEL,0,0,0); ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x); ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetString(0,n,OBJPROP_TEXT,t); ObjectSetInteger(0,n,OBJPROP_COLOR,c); ObjectSetInteger(0,n,OBJPROP_FONTSIZE,s);
   ObjectSetString(0,n,OBJPROP_FONT,"Consolas"); ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER); ObjectSetInteger(0,n,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
}
void CreateButton(string n,string t,int x,int y,int w,int h,color bg,color tc){
   if(ObjectFind(0,n)<0)ObjectCreate(0,n,OBJ_BUTTON,0,0,0); ObjectSetInteger(0,n,OBJPROP_XDISTANCE,x); ObjectSetInteger(0,n,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,n,OBJPROP_XSIZE,w); ObjectSetInteger(0,n,OBJPROP_YSIZE,h); ObjectSetString(0,n,OBJPROP_TEXT,t);
   ObjectSetInteger(0,n,OBJPROP_COLOR,tc); ObjectSetInteger(0,n,OBJPROP_BGCOLOR,bg); ObjectSetInteger(0,n,OBJPROP_BORDER_COLOR,clrGray);
   ObjectSetInteger(0,n,OBJPROP_FONTSIZE,runtimeFontSize); ObjectSetString(0,n,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,n,OBJPROP_CORNER,CORNER_LEFT_UPPER); ObjectSetInteger(0,n,OBJPROP_BACK,false); ObjectSetInteger(0,n,OBJPROP_SELECTABLE,true); ObjectSetInteger(0,n,OBJPROP_SELECTED,false);
}
void DeleteAllObjects(){
   for(int i=ObjectsTotal(-1)-1;i>=0;i--){string n=ObjectName(i);
      if(StringFind(n,"RBG_")==0||StringFind(n,"PR_")==0||StringFind(n,"PL_")==0||StringFind(n,"SG_")==0||
         StringFind(n,"PC_")==0||StringFind(n,"GP_")==0||StringFind(n,"GT_")==0||StringFind(n,"RS_")==0||
         StringFind(n,"SR_")==0||StringFind(n,"AV_")==0||StringFind(n,"WN_")==0||StringFind(n,"H_")==0||
         StringFind(n,"BB_")==0||StringFind(n,"BK_")==0||StringFind(n,"BS_")==0||StringFind(n,"BX_")==0||
         StringFind(n,"HDR_")==0||StringFind(n,"Header")==0||
         StringFind(n,"M1")==0||StringFind(n,"M2")==0||
         n=="F-"||n=="F+"||n=="AUTO"||n=="ALERT"||StringFind(n,"L")==0) ObjectDelete(0,n);
   }
}

// ===== TRAILING =====
void ManageTrailingStops(){
   for(int t=trailCount-1;t>=0;t--){bool f=false;for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderTicket()==trailData[t].ticket){f=true;break;}}if(!f){for(int k=t;k<trailCount-1;k++)trailData[k]=trailData[k+1];trailCount--;}}
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber||(OrderType()!=OP_BUY&&OrderType()!=OP_SELL))continue;
      int ti=-1; for(int t=0;t<trailCount;t++){if(trailData[t].ticket==OrderTicket()){ti=t;break;}}
      double atH=iATR(OrderSymbol(),PERIOD_H1,ATR_Period,0);if(atH<=0)continue;bool b=(OrderType()==OP_BUY);
      double cp=b?SymbolInfoDouble(OrderSymbol(),SYMBOL_BID):SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK);
      double op=OrderOpenPrice(),cs=OrderStopLoss(),pp=b?(cp-op):(op-cp);int dg=(int)MarketInfo(OrderSymbol(),MODE_DIGITS);
      if(ti<0){ti=trailCount;trailData[ti].ticket=OrderTicket();trailData[ti].peak=cp;trailData[ti].active=false;trailCount++;}
      if(b){if(cp>trailData[ti].peak)trailData[ti].peak=cp;}else{if(cp<trailData[ti].peak)trailData[ti].peak=cp;}
      if(!trailData[ti].active&&pp>=atH*1.0){trailData[ti].active=true;}
      if(trailData[ti].active){double ns;int sl=(int)MarketInfo(OrderSymbol(),MODE_STOPLEVEL);
         if(b){ns=trailData[ti].peak-atH*0.8;if(ns>cs+atH*0.2||cs==0){ns=NormalizeDouble(ns,dg);double mn=cp-sl*SymbolInfoDouble(OrderSymbol(),SYMBOL_POINT);if(ns<mn)ns=mn;OrderModify(OrderTicket(),op,ns,OrderTakeProfit(),0,clrWhite);}}
         else{ns=trailData[ti].peak+atH*0.8;if(ns<cs-atH*0.2||cs==0){ns=NormalizeDouble(ns,dg);double mx=cp+sl*SymbolInfoDouble(OrderSymbol(),SYMBOL_POINT);if(ns>mx)ns=mx;OrderModify(OrderTicket(),op,ns,OrderTakeProfit(),0,clrWhite);}}
      }
   }
}

// ===== TRADING =====
void OpenTrade(string sym,int type){
   if(!IsTradeAllowed()||!SymbolSelect(sym,true))return;int pc=0;
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()==MagicNumber&&(OrderType()==OP_BUY||OrderType()==OP_SELL))pc++;}
   if(pc>=runtimeMaxPos)return;for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()==sym&&OrderMagicNumber()==MagicNumber&&OrderType()==type)return;}
   double ask=SymbolInfoDouble(sym,SYMBOL_ASK),bid=SymbolInfoDouble(sym,SYMBOL_BID);if(ask<=0||bid<=0)return;
   double lot=NormalizeDouble(LotSize,2),minL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MIN),maxL=SymbolInfoDouble(sym,SYMBOL_VOLUME_MAX);
   if(lot<minL)lot=minL;if(lot>maxL)lot=maxL;double at=iATR(sym,PERIOD_H1,ATR_Period,0),p=(type==OP_BUY)?ask:bid,sl=0,tp=0;
   if(at>0){sl=(type==OP_BUY)?p-at*ATR_SL_Mult:p+at*ATR_SL_Mult;tp=(type==OP_BUY)?p+at*ATR_TP_Mult:p-at*ATR_TP_Mult;int d=(int)MarketInfo(sym,MODE_DIGITS);sl=NormalizeDouble(sl,d);tp=NormalizeDouble(tp,d);}
   int t=OrderSend(sym,type,lot,p,Slippage,sl,tp,"CCS",MagicNumber,0,clrNONE);if(t<=0){t=OrderSend(sym,type,lot,p,Slippage,0,0,"CCS",MagicNumber,0,clrNONE);if(t>0&&at>0&&OrderSelect(t,SELECT_BY_TICKET)){int d2=(int)MarketInfo(sym,MODE_DIGITS);sl=(type==OP_BUY)?OrderOpenPrice()-at*ATR_SL_Mult:OrderOpenPrice()+at*ATR_SL_Mult;tp=(type==OP_BUY)?OrderOpenPrice()+at*ATR_TP_Mult:OrderOpenPrice()-at*ATR_TP_Mult;OrderModify(t,OrderOpenPrice(),NormalizeDouble(sl,d2),NormalizeDouble(tp,d2),0,clrNONE);}}
}
void CloseSymbol(string s){for(int i=OrdersTotal()-1;i>=0;i--){if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=s||OrderMagicNumber()!=MagicNumber)continue;double cp;color ac;if(OrderType()==OP_BUY){cp=SymbolInfoDouble(s,SYMBOL_BID);ac=clrRed;}else{cp=SymbolInfoDouble(s,SYMBOL_ASK);ac=clrBlue;}if(OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac)){for(int tt=trailCount-1;tt>=0;tt--){if(trailData[tt].ticket==OrderTicket()){for(int k=tt;k<trailCount-1;k++)trailData[k]=trailData[k+1];trailCount--;break;}}}}}
void CloseAllPositions(){for(int i=OrdersTotal()-1;i>=0;i--){if(!OrderSelect(i,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()!=MagicNumber)continue;double cp;color ac;if(OrderType()==OP_BUY){cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_BID);ac=clrRed;}else{cp=SymbolInfoDouble(OrderSymbol(),SYMBOL_ASK);ac=clrBlue;}OrderClose(OrderTicket(),OrderLots(),cp,Slippage,ac);}}
void RunAutoTrade(){for(int i=0;i<totalPairs;i++){if(ccsData[i].signal!=2&&ccsData[i].signal!=-2)continue;int dt=(ccsData[i].signal==2)?OP_BUY:OP_SELL,ot=(ccsData[i].signal==2)?OP_SELL:OP_BUY;bool hD=false,hO=false;
   for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderSymbol()!=pairs[i]||OrderMagicNumber()!=MagicNumber)continue;if(OrderType()==dt)hD=true;if(OrderType()==ot)hO=true;}
   if(hO){CloseSymbol(pairs[i]);Sleep(200);}if(hD)continue;int tt=0;for(int j=0;j<OrdersTotal();j++){if(!OrderSelect(j,SELECT_BY_POS,MODE_TRADES))continue;if(OrderMagicNumber()==MagicNumber&&(OrderType()==OP_BUY||OrderType()==OP_SELL))tt++;}if(tt>=runtimeMaxPos)break;OpenTrade(pairs[i],dt);}
}
void CheckAlerts(){for(int i=0;i<totalPairs;i++){int s=ccsData[i].signal;if(s!=2&&s!=-2)continue;string d=(s==2)?"SB":"SS";
   if(lastAlertSignal[i]==d&&TimeCurrent()-lastAlertTime[i]<600)continue;lastAlertSignal[i]=d;lastAlertTime[i]=TimeCurrent();
   string w=(StringLen(ccsData[i].warning)>0)?"["+ccsData[i].warning+"]":"";
   string m="CCS:"+d+" "+pairs[i]+" G:"+DoubleToString(MathAbs(ccsData[i].ccyGap),1)+" GT:"+IntegerToString(ccsData[i].gateBull)+"/"+IntegerToString(ccsData[i].gateBear)+" R:"+DoubleToString(ccsData[i].rsi,1)+" "+IntegerToString(MathAbs(ccsData[i].score))+"/10"+w;
   if(alertON){Alert(m);SendNotification(m);}Print(m);}}
//+------------------------------------------------------------------+
