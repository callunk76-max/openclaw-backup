//+------------------------------------------------------------------+
//|                                        NexusReversalEA.mq4        |
//|                                    Strategy: Oscillation Catcher  |
//|                                          EURUSD & GBPUSD Only     |
//+------------------------------------------------------------------+
#property copyright "Callunk"
#property version   "2.11"
#property strict
#property description "Nexus Reversal EA - Oscillation Catcher"
#property description "EURUSD & GBPUSD scalping on M5 timeframe"
#property description ""
#property description "HOW IT WORKS:"
#property description "1. Places BuyStop & SellStop simultaneously"
#property description "2. Price hits SellStop → Sell opens, BuyStop trails price down"
#property description "3. Price reverses & BuyStop triggers → Sell closes, Buy opens"
#property description "4. SellStop now trails. Cycle repeats."
#property description ""
#property description "Spread-aware: force-close if spread blocks reversal."
#property description "Toleransi: jika spread terlalu besar untuk posisi lawan, current position force close via market."

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                  |
//+------------------------------------------------------------------+
input string   s1_settings        = "==== GRID SETTINGS ====";   // ==== GRID SETTINGS ====
input double   InitialGridPips    = 30.0;     // Initial gap (pips) between BuyStop & SellStop
input double   TrailPips          = 12.0;     // Trailing distance (pips) for reversal trigger
input double   MinOffset          = 5.0;      // Min distance (pips) from current price

input string   s2_money           = "==== MONEY MANAGEMENT ====";// ==== MONEY MANAGEMENT ====
input double   LotSize            = 0.01;     // Fixed lot size
input bool     UseAutoLot         = false;    // Auto lot based on risk %
input double   RiskPercent        = 1.0;      // Risk % per trade (if AutoLot=true)

input string   s3_filters         = "==== FILTERS ====";       // ==== FILTERS ====
input bool     AllowEURUSD        = true;     // Trade EURUSD
input bool     AllowGBPUSD        = true;     // Trade GBPUSD
input int      SpreadLimitEntry   = 25;       // Max spread (points) untuk entry baru
input int      SpreadMaxForce     = 40;       // Max spread (points) - force close jika reversal terblokir
input bool     UseTimeFilter      = false;    // Trade only during certain hours
input int      StartHour          = 8;        // Server start hour (0-23)
input int      EndHour            = 20;       // Server end hour (0-23)

input string   s4_advanced        = "==== ADVANCED ====";      // ==== ADVANCED ====
input int      MagicNumber        = 240502;    // EA magic number
input int      Slippage           = 3;         // Max slippage (points)
input bool     CloseOnFriday      = true;     // Close all at Friday close
input int      FridayCloseHour    = 21;       // Friday close hour (server time)
input int      BarsSinceLevel     = 3;         // Jumlah bar M5 tanpa trigger sebelum force close

//+------------------------------------------------------------------+
//| GLOBALS                                                           |
//+------------------------------------------------------------------+
int    g_magic;
double g_point;
double g_initialGrid;
double g_trailPips;
double g_minOffset;
double g_lot;
int    g_slippage;
int    g_maxSpreadForce;
int    g_spreadEntryLimit;

// State per symbol
string g_symbol;
int    g_ticketBuyStop;   // Pending BuyStop ticket
int    g_ticketSellStop;  // Pending SellStop ticket
int    g_ticketPosition;  // Active position ticket
int    g_positionType;    // -1=none, OP_BUY, OP_SELL
double g_extremePrice;    // Tracked extreme (lowest Bid for sell, highest Ask for buy)
double g_entryPrice;      // Position open price
int    g_lastBarTime;     // For new-bar detection
int    g_barsSinceLevelCross; // Bars since price crossed reversal level
double g_reversalLevel;   // The level where reversal should happen
bool   g_levelCrossed;    // Whether price has crossed reversal level

// Profit tracker
double g_totalClosedProfit;
int    g_totalTrades;
int    g_winningTrades;

//+------------------------------------------------------------------+
//| INIT                                                              |
//+------------------------------------------------------------------+
int OnInit()
{
   // Validate symbol
   string sym = Symbol();
   if (sym != "EURUSD" && sym != "GBPUSD")
   {
      Print("❌ This EA only works on EURUSD and GBPUSD. Current symbol: ", sym);
      return INIT_PARAMETERS_INCORRECT;
   }
   
   g_magic = MagicNumber;
   g_symbol = sym;
   g_slippage = Slippage;
   g_point = Point;
   g_lastBarTime = 0;
   g_barsSinceLevelCross = 0;
   g_reversalLevel = 0;
   g_levelCrossed = false;
   
   g_maxSpreadForce  = SpreadMaxForce;
   g_spreadEntryLimit = SpreadLimitEntry;
   
   // Init profit tracker
   g_totalClosedProfit = 0;
   g_totalTrades = 0;
   g_winningTrades = 0;
   
   // Pip adjustment (5-digit brokers use 10x)
   g_initialGrid = AdjustPips(InitialGridPips);
   g_trailPips   = AdjustPips(TrailPips);
   g_minOffset   = AdjustPips(MinOffset);
   
   // Validate trails
   if (g_trailPips <= g_minOffset)
   {
      g_trailPips = g_minOffset + g_point;
      Print("⚠️ TrailPips adjusted to MinOffset+1 pip");
   }
   if (g_initialGrid <= g_trailPips * 2)
   {
      g_initialGrid = g_trailPips * 2 + AdjustPips(10);
      Print("⚠️ InitialGrid adjusted to 2x TrailPips + 10 pips");
   }
   
   // Lot size
   g_lot = LotSize;
   if (UseAutoLot)
   {
      double accBalance = AccountBalance();
      double riskMoney  = accBalance * RiskPercent / 100.0;
      double tickValue  = MarketInfo(sym, MODE_TICKVALUE);
      double pipValue   = tickValue / g_point;
      if (pipValue > 0)
      {
         g_lot = NormalizeDouble(riskMoney / (TrailPips * pipValue), 2);
         double minLot = MarketInfo(sym, MODE_MINLOT);
         double maxLot = MarketInfo(sym, MODE_MAXLOT);
         g_lot = MathMin(MathMax(g_lot, minLot), maxLot);
      }
      Print("💰 Auto lot: ", g_lot, " (risk ", RiskPercent, "% of ", AccountBalance(), ")");
   }
   
   ResetState();
   Print("✅ NexusReversalEA initialized on ", g_symbol);
   Print("📏 Grid: ", InitialGridPips, " pips | Trail: ", TrailPips, " pips | Lot: ", g_lot);
   Print("📊 SpreadLimitEntry: ", SpreadLimitEntry, " | SpreadMaxForce: ", SpreadMaxForce);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| DEINIT                                                            |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("🔌 EA removed on ", g_symbol);
}

//+------------------------------------------------------------------+
//| TICK                                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   // --- Validate symbol ---
   if (g_symbol != Symbol()) return;
   if (!AllowEURUSD && g_symbol == "EURUSD") return;
   if (!AllowGBPUSD && g_symbol == "GBPUSD") return;
   
   // --- Time filter ---
   if (UseTimeFilter)
   {
      int hour = Hour();
      if (StartHour < EndHour)
      {
         if (hour < StartHour || hour >= EndHour) return;
      }
      else
      {
         if (hour < StartHour && hour >= EndHour) return;
      }
   }
   
   // --- Friday close check ---
   if (CloseOnFriday && DayOfWeek() == 5 && Hour() >= FridayCloseHour)
   {
      CloseAllOrders();
      return;
   }
   
   // --- New bar detection (M5) ---
   int currentBarTime = iTime(g_symbol, PERIOD_M5, 0);
   bool isNewBar = (currentBarTime != g_lastBarTime);
   if (isNewBar)
   {
      g_lastBarTime = currentBarTime;
      if (g_levelCrossed) g_barsSinceLevelCross++;
   }
   
   // --- Scan orders ---
   ScanOrders();
   
   // --- State machine ---
   if (g_positionType == -1)
   {
      HandleIdle();
   }
   else if (g_positionType == OP_SELL)
   {
      HandleSellPosition();
   }
   else if (g_positionType == OP_BUY)
   {
      HandleBuyPosition();
   }
}

//+------------------------------------------------------------------+
//| UTILITY: Adjust pips for digit factor                             |
//+------------------------------------------------------------------+
double AdjustPips(double pips)
{
   if (Digits == 3 || Digits == 5)
      return pips * 10 * g_point;
   return pips * g_point;
}

//+------------------------------------------------------------------+
//| UTILITY: Convert price to pips                                   |
//+------------------------------------------------------------------+
double PriceToPips(double price)
{
   if (Digits == 3 || Digits == 5)
      return price / (10 * g_point);
   return price / g_point;
}

//+------------------------------------------------------------------+
//| Reset internal state                                              |
//+------------------------------------------------------------------+
void ResetState()
{
   g_ticketBuyStop   = -1;
   g_ticketSellStop  = -1;
   g_ticketPosition  = -1;
   g_positionType    = -1;
   g_extremePrice     = 0;
   g_entryPrice       = 0;
   g_reversalLevel    = 0;
   g_levelCrossed     = false;
   g_barsSinceLevelCross = 0;
   g_initialBuyStopPrice  = 0;
   g_initialSellStopPrice = 0;
}

//+------------------------------------------------------------------+
//| Scan all orders for our MagicNumber                               |
//+------------------------------------------------------------------+
void ScanOrders()
{
   int foundBuyStop  = -1;
   int foundSellStop = -1;
   int foundPos      = -1;
   int posType       = -1;
   double entryPx    = 0;
   
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (OrderMagicNumber() != g_magic) continue;
      if (OrderSymbol() != g_symbol) continue;
      
      switch (OrderType())
      {
         case OP_BUYSTOP:  foundBuyStop  = OrderTicket(); break;
         case OP_SELLSTOP: foundSellStop = OrderTicket(); break;
         case OP_BUY:
            foundPos = OrderTicket();
            posType  = OP_BUY;
            entryPx  = OrderOpenPrice();
            break;
         case OP_SELL:
            foundPos = OrderTicket();
            posType  = OP_SELL;
            entryPx  = OrderOpenPrice();
            break;
      }
   }
   
   // --- Count all market positions (HEDGING: bisa ada 2 posisi!) ---
   int countBuy  = 0;
   int countSell = 0;
   int ticketBuyPos  = -1;
   int ticketSellPos = -1;
   datetime timeBuyPos  = 0;
   datetime timeSellPos = 0;
   
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (OrderMagicNumber() != g_magic) continue;
      if (OrderSymbol() != g_symbol) continue;
      
      if (OrderType() == OP_BUY)
      {
         countBuy++;
         ticketBuyPos = OrderTicket();
         timeBuyPos   = OrderOpenTime();
      }
      else if (OrderType() == OP_SELL)
      {
         countSell++;
         ticketSellPos = OrderTicket();
         timeSellPos   = OrderOpenTime();
      }
   }
   
   // Pilih posisi mana yang jadi "main position":
   if (countBuy + countSell == 0)
   {
      foundPos = -1;
      posType  = -1;
      entryPx  = 0;
   }
   else if (countBuy + countSell == 1)
   {
      foundPos = (countBuy == 1) ? ticketBuyPos : ticketSellPos;
      posType  = (countBuy == 1) ? OP_BUY : OP_SELL;
      if (OrderSelect(foundPos, SELECT_BY_TICKET)) entryPx = OrderOpenPrice();
   }
   else
   {
      // DUA posisi! Pending order baru trigger.
      // Ambil yang terakhir dibuka, tutup posisi LAMA.
      int oldTicket, newTicket, newType;
      
      if (timeBuyPos > timeSellPos)
      {
         newTicket = ticketBuyPos;
         newType   = OP_BUY;
         oldTicket = ticketSellPos;
      }
      else
      {
         newTicket = ticketSellPos;
         newType   = OP_SELL;
         oldTicket = ticketBuyPos;
      }
      
      // Tutup posisi LAMA via market
      CloseOrder(oldTicket);
      Print("🔄 Reversal: new ", (newType == OP_BUY ? "BUY" : "SELL"), " appeared, old position closed");
      
      foundPos = newTicket;
      posType  = newType;
      if (OrderSelect(newTicket, SELECT_BY_TICKET)) entryPx = OrderOpenPrice();
   }
   
   // --- Check if our position disappeared externally ---
   if (foundPos < 0 && g_ticketPosition > 0)
   {
      Print("❌ Position closed externally on ", g_symbol, ". Resetting.");
      ResetState();
      DeletePendingOrders();
      return;
   }
   
   // --- Detect state change from IDLE to having position (initial pending order triggered) ---
   if (g_positionType == -1 && foundPos > 0 && posType != -1)
   {
      g_ticketPosition = foundPos;
      g_positionType   = posType;
      g_entryPrice     = (OrderSelect(foundPos, SELECT_BY_TICKET)) ? OrderOpenPrice() : 0;
      g_extremePrice   = (posType == OP_BUY) ? Ask : Bid;
      DeletePendingOrders();
      Print("🔓 Entry: ", (posType == OP_BUY ? "BUY" : "SELL"), " at ", g_entryPrice);
      return;
   }
   
   // --- Update state ---
   g_ticketBuyStop   = foundBuyStop;
   g_ticketSellStop  = foundSellStop;
   g_ticketPosition  = foundPos;
   g_positionType    = posType;
   g_entryPrice      = entryPx;
   
   // Update extreme price
   if (posType == OP_SELL)
   {
      if (g_extremePrice == 0) g_extremePrice = Bid;
      else if (Bid < g_extremePrice && !g_levelCrossed)
      {
         g_extremePrice = Bid;
         g_barsSinceLevelCross = 0;
      }
   }
   else if (posType == OP_BUY)
   {
      if (g_extremePrice == 0) g_extremePrice = Ask;
      else if (Ask > g_extremePrice && !g_levelCrossed)
      {
         g_extremePrice = Ask;
         g_barsSinceLevelCross = 0;
      }
   }
}

//+------------------------------------------------------------------+
//| IDLE: No position → place initial BuyStop & SellStop              |
//+------------------------------------------------------------------+
double g_initialBuyStopPrice  = 0;
double g_initialSellStopPrice = 0;

void HandleIdle()
{
   int spread = (int)(Ask - Bid) / g_point;
   
   // ✅ Jika kedua pending order sudah ada, diamkan! Jangan diotak-atik.
   if (g_ticketBuyStop > 0 && g_ticketSellStop > 0)
   {
      string info = StringFormat("BuyStop: %.5f | SellStop: %.5f\nSpread: %d pts | Limit: %d pts\n✅ Pending STATIC - menunggu harga",
         g_initialBuyStopPrice, g_initialSellStopPrice, spread, g_spreadEntryLimit);
      ShowDashboard(info);
      return;
   }
   
   // Bersihkan pending order yang menggantung
   DeletePendingOrders();
   g_ticketBuyStop  = -1;
   g_ticketSellStop = -1;
   g_extremePrice   = 0;
   
   // CEK SPREAD — skip entry if spread too wide
   int spread = (int)(Ask - Bid) / g_point;
   if (spread > g_spreadEntryLimit)
   {
      ShowDashboard("⏳ Spread: " + (string)spread + " pts (limit: " + (string)g_spreadEntryLimit + ")", "Menunggu spread normal...");
      return;
   }
   
   // Get minimum stop level from broker
   double minDist = MarketInfo(g_symbol, MODE_STOPLEVEL) * g_point;
   if (minDist < 2 * g_point) minDist = 2 * g_point;
   
   // Calculate pending order prices
   double halfGrid = g_initialGrid / 2.0;
   double midPrice = (Ask + Bid) / 2.0;
   
   double buyStopPrice  = NormalizeDouble(midPrice + halfGrid, Digits);
   double sellStopPrice = NormalizeDouble(midPrice - halfGrid, Digits);
   
   // Ensure minimum distance from current price
   if (buyStopPrice <= Ask + minDist)
      buyStopPrice = Ask + minDist + g_point;
   if (sellStopPrice >= Bid - minDist)
      sellStopPrice = Bid - minDist - g_point;
   
   // Place BuyStop
   int ticket = OrderSend(g_symbol, OP_BUYSTOP, g_lot, buyStopPrice, g_slippage, 0, 0, "NexusRev", g_magic, 0, clrGreen);
   if (ticket > 0)
   {
      g_ticketBuyStop = ticket;
      g_initialBuyStopPrice = buyStopPrice;
      Print("📗 BuyStop placed at ", buyStopPrice, " (spread: ", spread, " pts)");
   }
   else
   {
      Print("❌ BuyStop failed: ", GetLastError());
   }
   
   // Place SellStop
   ticket = OrderSend(g_symbol, OP_SELLSTOP, g_lot, sellStopPrice, g_slippage, 0, 0, "NexusRev", g_magic, 0, clrRed);
   if (ticket > 0)
   {
      g_ticketSellStop = ticket;
      g_initialSellStopPrice = sellStopPrice;
      Print("📕 SellStop placed at ", sellStopPrice);
   }
   else
   {
      Print("❌ SellStop failed: ", GetLastError());
   }
   
   string info = StringFormat("BuyStop: %.5f | SellStop: %.5f\nGrid: %.0f pips | Lot: %.2f\nSpread: %d pts | Limit: %d pts",
      buyStopPrice, sellStopPrice, InitialGridPips, g_lot, spread, g_spreadEntryLimit);
   ShowDashboard(info, "📗 Menunggu entry...");
}

//+------------------------------------------------------------------+
//| SELL position active → Trail BuyStop for reversal                 |
//+------------------------------------------------------------------+
void HandleSellPosition()
{
   // --- Update extreme price (lowest Bid reached) ---
   if (!g_levelCrossed)
   {
      if (Bid < g_extremePrice) g_extremePrice = Bid;
   }
   
   // --- Calculate trail level for reversal ---
   double theoreticalBuyStopLevel = g_extremePrice + g_trailPips;
   g_reversalLevel = theoreticalBuyStopLevel;
   
   // --- Cek spread saat ini ---
   int spread = (int)(Ask - Bid) / g_point;
   
   // --- FORCE CLOSE CHECK #1: Price already crossed reversal level ---
   // Kalau harga (Bid) udah melewati level reversal, force close langsung
   // Nggak perlu nunggu BuyStop trigger — spread mungkin ngeblok
   if (Bid >= theoreticalBuyStopLevel)
   {
      Print("⚠️ FORCE CLOSE (SELL): Bid crossed reversal level ", DoubleToString(theoreticalBuyStopLevel, Digits),
            " | spread: ", spread, " pts");
      ForceCloseAndReset("SELL price reversal");
      return;
   }
   
   // --- FORCE CLOSE CHECK #2: Spread terlalu besar + sudah melewati level ---
   // Kalau Ask udah di atas reversal level tapi spread lebar, force close juga
   // BuyStop triggernya Ask, jadi kalo Ask di atas level + spread blok → force
   if (Ask >= theoreticalBuyStopLevel && spread > g_maxSpreadForce)
   {
      Print("⚠️ FORCE CLOSE (SELL): Ask crossed level but spread blocks (", spread, ")");
      ForceCloseAndReset("SELL spread blocked reversal");
      return;
   }
   
   // --- FORCE CLOSE CHECK #3: Level sudah crossed beberapa bar lalu ---
   // Artinya posisi lawan (BuyStop) gagal trigger karena spread atau alasan lain
   if (g_levelCrossed && g_barsSinceLevelCross >= BarsSinceLevel)
   {
      Print("⚠️ FORCE CLOSE (SELL): Level crossed for ", g_barsSinceLevelCross, " bars, no BuyStop triggered");
      ForceCloseAndReset("SELL pending order timeout");
      return;
   }
   
   // --- Track apakah level sudah dilewati ---
   if (Bid >= theoreticalBuyStopLevel - AdjustPips(2)) // toleransi 2 pip
   {
      if (!g_levelCrossed)
      {
         g_levelCrossed = true;
         g_barsSinceLevelCross = 0;
         Print("📊 SELL reversal level reached. Waiting for trigger/force... (spread: ", spread, ")");
      }
   }
   else
   {
      // Level not yet crossed
      g_levelCrossed = false;
      g_barsSinceLevelCross = 0;
   }
   
   // --- Delete any pending SellStop (no longer needed) ---
   if (g_ticketSellStop > 0)
   {
      DeleteOrder(g_ticketSellStop);
      g_ticketSellStop = -1;
   }
   
   // --- Place or update trailing BuyStop ---
   double buyStopPrice = theoreticalBuyStopLevel;
   
   double minDist = MarketInfo(g_symbol, MODE_STOPLEVEL) * g_point;
   if (minDist < 2 * g_point) minDist = 2 * g_point;
   
   if (buyStopPrice <= Ask + minDist)
      buyStopPrice = Ask + minDist + g_point;
   
   if (g_ticketBuyStop > 0)
   {
      if (OrderSelect(g_ticketBuyStop, SELECT_BY_TICKET))
      {
         if (MathAbs(OrderOpenPrice() - buyStopPrice) > g_point)
         {
            if (!OrderModify(g_ticketBuyStop, buyStopPrice, 0, 0, 0, clrGreen))
            {
               Print("⚠️ BuyStop modify failed: ", GetLastError());
               g_ticketBuyStop = -1; // Will be recreated below
            }
         }
      }
      else
      {
         g_ticketBuyStop = -1;
      }
   }
   
   if (g_ticketBuyStop < 0)
   {
      int ticket = OrderSend(g_symbol, OP_BUYSTOP, g_lot, buyStopPrice, g_slippage, 0, 0, "NexusRev", g_magic, 0, clrGreen);
      if (ticket > 0)
      {
         g_ticketBuyStop = ticket;
      }
      else
      {
         Print("❌ BuyStop trail failed: ", GetLastError());
      }
   }
   
   // --- Display ---
   string status = g_levelCrossed ? "⚠️ REVERSAL PENDING" : "⏳ Menunggu reversal";
   string forceWarn = "";
   if (g_levelCrossed)
      forceWarn = StringFormat("⏰ Force close: %d bar(s)", BarsSinceLevel - g_barsSinceLevelCross);
   
   // --- Build info string ---
   string info = StringFormat(
      "🔴 SELL  | Entry: %.5f  | Lots: %.2f\n"
      "Extreme Low: %.5f  (%.1f pips from Bid)\n"
      "Trail Level: %.5f  (%.0f pips from extreme)\n"
      "Current: Ask=%.5f  Bid=%.5f\n"
      "Spread: %d pts  %s",
      g_entryPrice, g_lot,
      g_extremePrice, PriceToPips(Bid - g_extremePrice),
      theoreticalBuyStopLevel, TrailPips,
      Ask, Bid,
      spread, forceWarn);
   ShowDashboard(info, status);
}

//+------------------------------------------------------------------+
//| BUY position active → Trail SellStop for reversal                 |
//+------------------------------------------------------------------+
void HandleBuyPosition()
{
   // --- Update extreme price (highest Ask reached) ---
   if (!g_levelCrossed)
   {
      if (Ask > g_extremePrice) g_extremePrice = Ask;
   }
   
   // --- Calculate trail level for reversal ---
   double theoreticalSellStopLevel = g_extremePrice - g_trailPips;
   g_reversalLevel = theoreticalSellStopLevel;
   
   // --- Cek spread saat ini ---
   int spread = (int)(Ask - Bid) / g_point;
   
   // --- FORCE CLOSE CHECK #1: Price already crossed reversal level ---
   if (Ask <= theoreticalSellStopLevel)
   {
      Print("⚠️ FORCE CLOSE (BUY): Ask crossed reversal level ", DoubleToString(theoreticalSellStopLevel, Digits),
            " | spread: ", spread, " pts");
      ForceCloseAndReset("BUY price reversal");
      return;
   }
   
   // --- FORCE CLOSE CHECK #2: Spread terlalu besar ---
   if (Bid <= theoreticalSellStopLevel && spread > g_maxSpreadForce)
   {
      Print("⚠️ FORCE CLOSE (BUY): Bid crossed level but spread blocks (", spread, ")");
      ForceCloseAndReset("BUY spread blocked reversal");
      return;
   }
   
   // --- FORCE CLOSE CHECK #3: Level sudah crossed beberapa bar lalu ---
   if (g_levelCrossed && g_barsSinceLevelCross >= BarsSinceLevel)
   {
      Print("⚠️ FORCE CLOSE (BUY): Level crossed for ", g_barsSinceLevelCross, " bars, no SellStop triggered");
      ForceCloseAndReset("BUY pending order timeout");
      return;
   }
   
   // --- Track apakah level sudah dilewati ---
   if (Ask <= theoreticalSellStopLevel + AdjustPips(2)) // toleransi 2 pip
   {
      if (!g_levelCrossed)
      {
         g_levelCrossed = true;
         g_barsSinceLevelCross = 0;
         Print("📊 BUY reversal level reached. Waiting for trigger/force... (spread: ", spread, ")");
      }
   }
   else
   {
      g_levelCrossed = false;
      g_barsSinceLevelCross = 0;
   }
   
   // --- Delete any pending BuyStop (no longer needed) ---
   if (g_ticketBuyStop > 0)
   {
      DeleteOrder(g_ticketBuyStop);
      g_ticketBuyStop = -1;
   }
   
   // --- Place or update trailing SellStop ---
   double sellStopPrice = theoreticalSellStopLevel;
   
   double minDist = MarketInfo(g_symbol, MODE_STOPLEVEL) * g_point;
   if (minDist < 2 * g_point) minDist = 2 * g_point;
   
   if (sellStopPrice >= Bid - minDist)
      sellStopPrice = Bid - minDist - g_point;
   
   if (g_ticketSellStop > 0)
   {
      if (OrderSelect(g_ticketSellStop, SELECT_BY_TICKET))
      {
         if (MathAbs(OrderOpenPrice() - sellStopPrice) > g_point)
         {
            if (!OrderModify(g_ticketSellStop, sellStopPrice, 0, 0, 0, clrRed))
            {
               Print("⚠️ SellStop modify failed: ", GetLastError());
               g_ticketSellStop = -1;
            }
         }
      }
      else
      {
         g_ticketSellStop = -1;
      }
   }
   
   if (g_ticketSellStop < 0)
   {
      int ticket = OrderSend(g_symbol, OP_SELLSTOP, g_lot, sellStopPrice, g_slippage, 0, 0, "NexusRev", g_magic, 0, clrRed);
      if (ticket > 0)
      {
         g_ticketSellStop = ticket;
      }
      else
      {
         Print("❌ SellStop trail failed: ", GetLastError());
      }
   }
   
   // --- Display ---
   string status = g_levelCrossed ? "⚠️ REVERSAL PENDING" : "⏳ Menunggu reversal";
   string forceWarn = "";
   if (g_levelCrossed)
      forceWarn = StringFormat("⏰ Force close: %d bar(s)", BarsSinceLevel - g_barsSinceLevelCross);
   
   // --- Build info string ---
   string info = StringFormat(
      "🟢 BUY   | Entry: %.5f  | Lots: %.2f\n"
      "Extreme High: %.5f  (%.1f pips from Ask)\n"
      "Trail Level: %.5f  (%.0f pips from extreme)\n"
      "Current: Ask=%.5f  Bid=%.5f\n"
      "Spread: %d pts  %s",
      g_entryPrice, g_lot,
      g_extremePrice, PriceToPips(g_extremePrice - Ask),
      theoreticalSellStopLevel, TrailPips,
      Ask, Bid,
      spread, forceWarn);
   ShowDashboard(info, status);
}

//+------------------------------------------------------------------+
//| TRACK CLOSED TRADE: update profit & statistics                    |
//+------------------------------------------------------------------+
void TrackClosedTrade(double pnl)
{
   g_totalClosedProfit += pnl;
   g_totalTrades++;
   if (pnl > 0) g_winningTrades++;
   
   Print("📊 Trade #", g_totalTrades, " closed: ", DoubleToString(pnl, 2), 
         " | Total: ", DoubleToString(g_totalClosedProfit, 2),
         " | WR: ", (g_totalTrades > 0 ? DoubleToString(100.0 * g_winningTrades / g_totalTrades, 1) : "0"), "%");
}

//+------------------------------------------------------------------+
//| SHOW DASHBOARD: tampilkan info lengkap di sudut kanan atas        |
//+------------------------------------------------------------------+
double g_maxEquity = 0;

void ShowDashboard(string stateInfo, string extraInfo = "")
{
   // Hitung floating P&L
   double floatPnl = 0;
   int openTrades = 0;
   if (g_ticketPosition > 0 && OrderSelect(g_ticketPosition, SELECT_BY_TICKET))
   {
      floatPnl = OrderProfit() + OrderSwap() + OrderCommission();
      openTrades = 1;
   }
   
   // Tracking max equity untuk drawdown
   double equity = AccountEquity();
   if (equity > g_maxEquity) g_maxEquity = equity;
   double dd = (g_maxEquity > 0) ? ((g_maxEquity - equity) / g_maxEquity * 100.0) : 0;
   
   // String helpers
   string winRate  = (g_totalTrades > 0) ? DoubleToString(100.0 * g_winningTrades / g_totalTrades, 1) + "%" : "-";
   string avgPnl   = (g_totalTrades > 0) ? DoubleToString(g_totalClosedProfit / g_totalTrades, 2) : "-";
   string totalPnl = DoubleToString(g_totalClosedProfit, 2);
   string floating = DoubleToString(floatPnl, 2);
   string ddStr    = DoubleToString(dd, 2) + "%";
   
   // Balik ke hitam/merah berdasarkan profit
   string sigilClosed = (g_totalClosedProfit >= 0) ? "+" : "";
   string sigilFloat  = (floatPnl >= 0) ? "+" : "";
   
   Comment(
      "═══════════ NEXUS REVERSAL EA ═══════════",
      "\n",
      "\n📈 Balance: $", DoubleToString(AccountBalance(), 2),
      "   💰 Equity: $", DoubleToString(equity, 2),
      "   📉 DD: ", ddStr,
      "\n",
      "\n── PROFIT ──",
      "\n💵 Closed P&L:  $", (g_totalClosedProfit >= 0 ? "+" : ""), totalPnl,
      "  (avg: $", avgPnl, ")",
      "\n🔵 Floating P&L: $", sigilFloat, floating,
      "\n📊 Trades: ", g_totalTrades, "   ✅ Win: ", g_winningTrades, "   📊 WR: ", winRate,
      "\n",
      "\n── POSISI ──",
      "\n", stateInfo,
      "\n",
      (extraInfo != "" ? ("\n" + extraInfo) : ""),
      "\n",
      "\n═══════════════════════════════════════"
   );
}

//+------------------------------------------------------------------+
//| FORCE CLOSE: Tutup posisi via market jika reversal terblokir      |
//+------------------------------------------------------------------+
void ForceCloseAndReset(string reason)
{
   // Tutup posisi market yang masih open
   if (g_ticketPosition > 0)
   {
      if (OrderSelect(g_ticketPosition, SELECT_BY_TICKET))
      {
         RefreshRates();
         double closePrice = (OrderType() == OP_BUY) ? Bid : Ask;
         
         if (OrderClose(g_ticketPosition, OrderLots(), closePrice, g_slippage, clrNONE))
         {
            double closedPnl = OrderProfit() + OrderSwap() + OrderCommission();
            TrackClosedTrade(closedPnl);
            Print("✅ Force close: ", reason, " | Profit: ", closedPnl);
         }
         else
         {
            Print("❌ Force close failed: ", GetLastError());
         }
      }
   }
   
   // Hapus pending orders
   DeletePendingOrders();
   
   // Reset state → balik ke IDLE, pasang pending baru di tick berikutnya
   ResetState();
}

//+------------------------------------------------------------------+
//| Close a single order (normal close)                               |
//+------------------------------------------------------------------+
void CloseOrder(int ticket)
{
   if (ticket < 0) return;
   if (!OrderSelect(ticket, SELECT_BY_TICKET)) return;
   
   RefreshRates();
   double closePrice = (OrderType() == OP_BUY) ? Bid : Ask;
   
   if (OrderClose(ticket, OrderLots(), closePrice, g_slippage, clrNONE))
   {
      double pnl = OrderProfit() + OrderSwap() + OrderCommission();
      TrackClosedTrade(pnl);
      Print("✅ Closed ", (OrderType() == OP_BUY ? "BUY" : "SELL"), " ticket ", ticket, " | P&L: ", DoubleToString(pnl, 2));
   }
   else
   {
      Print("❌ Close failed ticket ", ticket, " error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Close all orders for this EA/symbol                               |
//+------------------------------------------------------------------+
void CloseAllOrders()
{
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (OrderMagicNumber() != g_magic) continue;
      if (OrderSymbol() != g_symbol) continue;
      
      if (OrderType() == OP_BUY || OrderType() == OP_SELL)
      {
         CloseOrder(OrderTicket());
      }
   }
   
   DeletePendingOrders();
   ResetState();
   Print("🔚 All closed (end of session) on ", g_symbol);
}

//+------------------------------------------------------------------+
//| Delete all pending orders for this EA/symbol                      |
//+------------------------------------------------------------------+
void DeletePendingOrders()
{
   for (int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if (!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if (OrderMagicNumber() != g_magic) continue;
      if (OrderSymbol() != g_symbol) continue;
      
      if (OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP)
      {
         OrderDelete(OrderTicket());
      }
   }
   g_ticketBuyStop  = -1;
   g_ticketSellStop = -1;
}

//+------------------------------------------------------------------+
//| Delete a single pending order                                     |
//+------------------------------------------------------------------+
void DeleteOrder(int ticket)
{
   if (ticket < 0) return;
   if (OrderSelect(ticket, SELECT_BY_TICKET))
   {
      if (OrderType() == OP_BUYSTOP || OrderType() == OP_SELLSTOP)
      {
         OrderDelete(ticket);
      }
   }
}
//+------------------------------------------------------------------+
