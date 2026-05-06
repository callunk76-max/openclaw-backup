# CALLUNK CONFLUENCE SYSTEM (CCS)

> **Timeframe:** H1 (Bias/Trend) | M15 (Entry/Exit)  
> **Instruments:** Forex (Major & Cross)  
> **Author:** Callunk & Cuy

---

## 📐 1. CORE PHILOSOPHY

Lima indikator bukan 5 sinyal terpisah, tapi **5 lapis konfirmasi** yang saling mengunci.

**Flow Chart Rule:**
```
Currency Strength Gap ≥ 5  ─┬─→ Lolos → Cek EMA Gate H1
                             │         ↓
                             │      EMA Gate OK? → Cek SnR Level
                             │         ↓
                             │      SnR Konfirmasi? → Cek BB + RSI di M15
                             │         ↓
                             │      Entry → ATR untuk SL/TP
                             │
                             └─→ Gagal → SKIP (trading kosong)
```

---

## 🚦 2. LAYER 1 — EMA GATES (H1 Trend Filter)

Ini **pintu gerbang**, bukan sinyal eksekusi.

### EMA Setup
| EMA | Peran | Signifikansi |
|-----|-------|-------------|
| EMA 200 | **Gerbang Utama** — Bull/Bear Zone | Paling sakral, jangan dilawan |
| EMA 100 | Gerbang Sekunder | Konfirmasi trend menengah |
| EMA 50  | Medium Trend | Bias intraday |
| EMA 20  | Short-term Path | Jalan terdekat harga |

### Logic
```
H1 Candle CLOSE:

DI ATAS EMA 200 + 100 + 50 + 20 → 🟢 STRONG BULLISH (4/4 gate)
DI ATAS EMA 100 + 50 + 20       → 🟢 BULLISH (3/4 gate)
DI ATAS EMA 50 + 20             → 🟡 SLIGHTLY BULLISH (2/4 gate)
DI TENGAH-TENGAH                → 🔴 NO BIAS — Skip atau tunggu

(Untuk SELL tinggal kebalikannya)
```

### Konfirmasi Gap
Untuk buy signal, minimal **3 dari 4 gate** searah dengan GAP direction.

### Rule Penting
- **Jangan entry SELL** kalau harga di atas EMA200 (bear trap)
- **Jangan entry BUY** kalau harga di bawah EMA200 (bull trap)
- Kecuali ada konfirmasi SnR kuat + RSI extreme + candlestick reversal

---

## ⚡ 3. LAYER 2 — CURRENCY STRENGTH GAP (Macro Filter)

Bersumber dari sistem strength yang udah jalan.

### Rule
| Gap | Keputusan |
|-----|-----------|
| Gap ≥ 5 | ✅ AMAN — Lanjut konfirmasi |
| Gap ≥ 7 | 🟢 SANGAT KUAT — Prioritas tinggi |
| Gap < 5 | ❌ SKIP — Jangan paksakan |

### Pengecualian
Gap < 5 tapi tetap bisa dipertimbangkan jika:
- Terjadi **BB squeeze** (breakout imminent)
- Ada **SnR level super kuat** yang disentuh
- **Divergence RSI** jelas

---

## 🧱 4. LAYER 3 — SnR KEY LEVELS (Support & Resistance)

### Method: Multi-Timeframe Swing Point Detection

#### Level Utama — H1 Swing High/Low (SnR Primary)
- Deteksi **Swing High**: Higher High yang kemudian diikuti Lower High
- Deteksi **Swing Low**: Lower Low yang kemudian diikuti Higher Low
- Minimal 3 candle di kiri & kanan
- Level-level ini jadi **Support/Resistance utama**

#### Level Sekunder — M15 Swing High/Low (SnR Secondary)
- Swing points di M15 untuk entry yang lebih presisi
- Level-level ini untuk **entry zone** dan **SL placement** yang lebih ketat

#### Pivot Cluster Rule
- Saat ≥2 swing points (dari TF berbeda) mengumpul di harga yang sama → **Strong Zone**
- Saat ≥3 swing points → **Super Strong Zone** — konfirmasi prioritas tinggi

#### Mitigation Rule (Level Flip)
```
Level SUPPORT ditembus → menjadi RESISTANCE baru
Level RESISTANCE ditembus → menjadi SUPPORT baru
```
- Mitigasi hanya valid jika **candle CLOSE** di atas/bawah level (bukan wick)
- Level asli tetap dipertahankan di chart sebagai referensi

#### Market Structure Rule
```
Higher High (HH) + Higher Low (HL) = UPTREND
Lower High (LH) + Lower Low (LL) = DOWNTREND
```
Gunakan market structure H1 untuk menentukan bias sebelum entry M15.

#### Confluence Zone
Level SnR yang juga **dekat atau overlap dengan EMA** (terutama EMA50/100/200):
```
EMA + SnR di harga yang sama → ZONA SUPER STRONG
Harga sentuh zona ini → POTENSI REVERSAL/BREAKOUT TINGGI
```

---

## 📈 5. LAYER 4 — BB + RSI (Entry Trigger di M15)

### ATR + RSI Regime — Konteks Volatilitas

```
ATR TURUN  + RSI TINGGI  → 🟢 Tren naik stabil, volatilitas terkendali
                             → BUY aman, TP bisa lebih jauh

ATR NAIK   + RSI TINGGI  → 🟡 Tren naik TAPI volatilitas tinggi
                             → Rawan koreksi tajam, waspadai reversal
                             → SL diperlebar, TP1 diambil lebih cepat

ATR TURUN  + RSI TURUN   → ⚪ Pasar tenang, konsolidasi
                             → Jangan entry, tunggu breakout

ATR NAIK   + RSI TURUN   → 🔴 Tren turun dengan momentum
                             → SELL signal valid (jika konfirmasi lain)
```

**Cara pakai:**
- Cek ATR M15: bandingkan ATR sekarang dengan ATR 10 periode lalu (naik/turun)
- Cek RSI M15: relatif (tinggi > 60, rendah < 40)
- Gabungkan dua kondisi di atas untuk **menyesuaikan risk level**

> 💡 ATR yang naik cepat + RSI extreme = alarm reversal. Jangan entry tanpa konfirmasi candlestick yang jelas.

### Logika Dasar

#### BUY
```
1. Harga touch/slightly break LOWER BB
2. RSI < 30 (oversold) ATAU RSI turning up dari < 30
3. ATR + RSI Regime cocok (ATR turun+RSI naik atau ATR normal+RSI oversold)
4. Price mendekati SUPPORT (dari SnR Layer 3)
5. Candlestick reversal confirmation (hammer, bullish engulfing, pin bar)
```

#### SELL
```
1. Harga touch/slightly break UPPER BB
2. RSI > 70 (overbought) ATAU RSI turning down dari > 70
3. ATR + RSI Regime cocok (ATR turun+RSI turun atau ATR naik+RSI overbought)
4. Price mendekati RESISTANCE (dari SnR Layer 3)
5. Candlestick reversal confirmation (shooting star, bearish engulfing, pin bar)
```

#### BB Squeeze (Breakout)
```
1. BB Bandwidth menyempit (squeeze)
2. Tunggu breakout candle CLOSE di luar BB
3. RSI konfirmasi arah (break atas → RSI > 50 rising)
4. SnR level sudah dilewati
```

### Divergence Entry (Advanced)
```
RSI DIVERGENCE + SnR + BB:

BULLISH DIV:
- Harga bikin Lower Low, RSI bikin Higher Low
- Price dekat SUPPORT + lower BB
- Tunggu konfirmasi candle → BUY

BEARISH DIV:
- Harga bikin Higher High, RSI bikin Lower High
- Price dekat RESISTANCE + upper BB
- Tunggu konfirmasi candle → SELL
```

---

## 🛡️ 6. LAYER 5 — ATR RISK MANAGEMENT

### Stop Loss
```
SL = ATR × 1.5  (pada timeframe entry M15)

TAPI... SL tidak boleh melebihi:
- SnR terdekat (untuk BUY: di bawah support, untuk SELL: di atas resistance)
- Pilih jarak YANG LEBIH KETAT antara ATR-based vs SnR-based
```

### Take Profit

#### TP1 (50% posisi)
```
TP1 = Entry + (ATR × 2)
Atau SnR berikutnya (mana yang lebih dulu)
```

#### TP2 (50% posisi)
```
Trailing pakai EMA20 M15
Atau SnR berikutnya setelah TP1 tercapai
```

### Position Sizing (Option)
```
Lot = (Risk per Trade) / (SL dalam pip × nilai pip per lot)
Risk per Trade: 1-2% dari balance
```

---

## ✅ 7. FULL FLOW EKSEKUSI

### BUY SCENARIO CONTOH:

```
Step 1 — MACRO FILTER
├── Cek Strength: AUD = 8.57 vs USD = 0.86
├── GAP = 7.71 → ✅ AMAN
└── Pair = AUD/USD

Step 2 — BIAS H1
├── Harga di atas EMA 200 → ✅ Bull zone
├── Harga di atas EMA 100 → ✅
├── Harga di atas EMA 50  → ✅
├── Harga di atas EMA 20  → ✅
├── 4/4 Gate → STRONG BULLISH BIAS
└── GAP direction = BUY → ✅ Searah

Step 3 — SnR LEVEL
├── Support H1 terdekat di 0.6450
├── Harga saat ini: 0.6480
└── Ada Swing Low H1 di 0.6445 → Strong Support Zone

Step 4 — ENTRY M15
├── Harga turun ke 0.6460 (mendekati support zone)
├── Touch LOWER BB di M15
├── RSI = 28 (oversold) — TAPI cek ATR regime:
│   ├── ATR M15 skrg = 12 pip (10 periode lalu = 8 pip)
│   ├── ATR NAIK + RSI RENDAH → 🔴 Normalnya sinyal SELL (tren turun)
│   └── → HATI-HATI! Entry BUY di kondisi ini berisiko
├── TAPI ternyata ATR skrg = 8 pip (10 periode lalu = 12 pip)
│   └── ATR TURUN + RSI RENDAH → ⚪ Konsolidasi, tunggu konfirmasi lebih lanjut
├── Candlestick: Bullish Engulfing ✅
├── RSI mulai turning up dari 28 ✅
├── ATR TURUN + RSI mulai NAIK → 🟢 Transisi dari konsolidasi ke bullish ✅
└── → ENTRY BUY di 0.6460 ✅

Step 5 — RISK
├── SL: support di 0.6440 (20 pip)
├── ATR M15 = 8 pip, 1.5 × ATR = 12 pip → SL 12 pip (lebih ketat dari 20 pip) ✅
├── → SL dipasang 12 pip di bawah entry = 0.6448
├── TP1: 0.6460 + (8 × 2) = 0.6476
└── TP2: SnR berikutnya atau trailing EMA20
```

---

## ⚠️ 8. CAVEATS & DISKUSI

### Kelemahan Yang Perlu Dicatat:
1. **Lagging** — Semua indikator berbasis MA → delay di trend reversal mendadak
2. **Sideways Market** — BB + RSI bisa oscillate, EMA flat, SnR berkurang relevansinya
3. **Strong Trend** — RSI bisa stuck overbought/oversold, BB bisa terus digandoli
4. **News Event** — SnR bisa jebol dalam sekejap (NFP, FOMC, rate decision)

### Saran Mitigasi:
- Hindari trading 30 menit sebelum & 15 menit setelah news high impact
- Kalau ATR M15 naik > 50% dari rata-rata → curiga ada volatility spike → tunggu
- Kalau EMA 20/50/100 ribbon melebar → trending kuat → BB oversold/overbought bisa diabaikan

---

## 📁 9. FILE STRUCTURE REFERENSI

```
Trading/
├── strategies/
│   ├── callunk_confluence_system.md    ← Kamu disini
│   ├── rules/
│   │   ├── entry_rules.md
│   │   ├── exit_rules.md
│   │   └── risk_management.md
│   └── snr_logic.md
├── indicators/
│   └── ...
├── *.py
├── *.mq4
├── *.pine
└── ...
```

---

**Versi:** 1.0 — Draft Diskusi  
**Status:** ✏️ Belum diimplementasikan, masih review bareng
