# 📊 CCS Dashboard — Panduan Lengkap Kolom

## 1. SIGNAL — Arah Trading

| Tampilan | Score | Arti | Warna | Aksi |
|----------|-------|------|-------|------|
| **STRBUY** | ≥ 7 | Semua konfirmasi kuat, GAP & EMA searah | 🟢 Hijau Terang | ✅ Entry penuh / Auto Trade ON |
| **BUY** | ≥ 4 | Cukup konfirmasi, GAP positif | 🟢 Hijau Lembut | ✅ Bisa entry (50% lot) |
| **WAIT** | < 4 | GAP bagus tapi konfirmasi kurang | ⚪ Abu | ⏳ Tunggu konfirmasi tambahan |
| **SELL** | ≥ 4 | Cukup konfirmasi, GAP negatif | 🔴 Merah Lembut | ✅ Bisa entry (50% lot) |
| **STRSEL** | ≥ 7 | Semua konfirmasi bearish kuat | 🔴 Merah Terang | ✅ Entry penuh / Auto Trade ON |
| **WAIT** | — | GAP < 5 (NoGAP) | ⚪ Abu | ❌ Skip, gak ada bias arah |

> **Score breakdown:** GAP Gate (≥5) + EMA (+1~3) + BB+RSI (+1~2) + SnR (+1) + GAP bonus (+2) − Conflict (−2)

---

## 2. GAP — Currency Strength Difference

| Tampilan | Range | Arti | Warna |
|----------|-------|------|-------|
| **7.0 ~ 9.0** | Gap ≥ 7 | 🟢 Super kuat — kedua currency sangat timpang | 🟢 Hijau |
| **5.0 ~ 6.9** | Gap ≥ 5 | 🟢 Cukup kuat — bias arah valid | 🟢 Hijau |
| **0.0 ~ 4.9** | Gap < 5 | ⚪ Netral — bias lemah, NoGAP | ⚪ Abu |
| **5.0 ~ 9.0** | Gap ≤ -5 | 🔻 Bearish kuat — quote currency dominan | 🔴 Merah |

> **Cara hitung:** Tiap pair di D1 dapet score 0-9 dari posisi close dalam daily range.  
> Currency strength = rata-rata 7 pair per currency.  
> **GAP = Base_strength − Quote_strength** (tampil nilai absolut).  
> Sumber: `currency_strength.pine` (Callunk GIRAIA logic).

### Contoh
```
Pair AUDUSD → Base = AUD (8.0), Quote = USD (0.0) → GAP = 8.0 🟢
Pair USDJPY → Base = USD (0.0), Quote = JPY (7.0) → GAP = 7.0 🔴
```

---

## 3. GT — EMA Gates (H1)

| Tampilan | Arti | Warna |
|----------|------|-------|
| **4/0** | 4 EMA bullish, 0 bearish — **sangat kuat** | 🟢 Hijau |
| **3/1** | 3 EMA bullish — bias naik dominan | 🟢 Hijau |
| **2/2** | Seimbang — sideways / transisi | ⚪ Abu |
| **1/3** | 3 EMA bearish — bias turun dominan | 🔴 Merah |
| **0/4** | 4 EMA bearish — **sangat bearish** | 🔴 Merah |

**Detail EMA yang dicek:**

| EMA | Periode | Peran |
|-----|---------|-------|
| **EMA20** | 20 | Short-term path — jalan terdekat |
| **EMA50** | 50 | Medium trend — bias intraday |
| **EMA100** | 100 | Gerbang sekunder — trend menengah |
| **EMA200** | 200 | **Gerbang utama** — bull/bear zone |

> **Logic:** Harga H1 close di atas EMA → +1 gate bullish.  
> Scoring: 4/4 gate = +3, 3/4 = +2, 2/4 = +1.

### Conflict Penalty
Jika EMA gates **berlawanan arah dengan GAP**, kena **−2 penalty**:
```
GAP = +7.0 (bullish) tapi GT = 0/4 (bearish) → Score −2
GAP = −6.0 (bearish) tapi GT = 4/0 (bullish) → Score −2
```

---

## 4. RSI — Relative Strength Index (H1)

| Tampilan | Range | Arti | Warna |
|----------|-------|------|-------|
| **< 30.0** | 0.0 ~ 29.9 | **Oversold** — potensi reversal naik | 🟢 Hijau |
| **30.0 ~ 70.0** | 30.0 ~ 69.9 | Normal — tidak ada sinyal reversal | ⚪ Putih |
| **> 70.0** | 70.0 ~ 100.0 | **Overbought** — potensi reversal turun | 🔴 Merah |

**Parameter:**
- Periode: 14
- Timeframe: **H1**
- Harga: Close

### Kombinasi dengan BB (Entry Trigger)
```
RSI < 30 + BB LOW touch  = +2 (sinyal BUY kuat)
RSI < 30 saja / BB saja  = +1 (cukup)
RSI turning up            = +1 (momentum shift)

RSI > 70 + BB HIGH touch = +2 (sinyal SELL kuat)
RSI > 70 saja / BB saja  = +1 (cukup)
RSI turning down         = +1 (momentum shift)
```

---

## 5. REG — ATR + RSI Regime (H1)

| Tampilan | Kondisi | Arti | Warna |
|----------|---------|------|-------|
| **StBl** | ATR ↓ + RSI > 60 | **Stable Bullish** — tren naik stabil, volatilitas turun | 🟢 Hijau Muda |
| **StBe** | ATR ↓ + RSI < 40 | **Stable Bearish** — tren turun stabil | 🟠 Salmon |
| **VHiR** | ATR ↑ + RSI > 60 | **Volatile High RSI** — tren naik tp volatilitas tinggi, rawan koreksi | 🟡 Orange |
| **VLoR** | ATR ↑ + RSI < 40 | **Volatile Low RSI** — tren turun dgn volatilitas tinggi, rawan bounce | 🟡 Orange |
| **Norm** | Lainnya | **Normal** — gak ada kondisi khusus | ⚪ Abu |

### Interpretasi untuk Entry:

| Regime | Implikasi |
|--------|-----------|
| **StBl** 🟢 | BUY aman — TP bisa jauh, volatilitas terkendali |
| **StBe** 🟠 | SELL aman — TP bisa jauh |
| **VHiR** 🟡 | ⚠️ Hati-hati BUY! Volatilitas tinggi, siap-siap TP lebih cepat |
| **VLoR** 🟡 | ⚠️ Hati-hati SELL! Bisa reversal mendadak |
| **Norm** ⚪ | Kondisi normal — ikuti signal seperti biasa |

---

## 6. WARN — Warning Text

| Tampilan | Kondisi | Level | Warna |
|----------|---------|-------|-------|
| **VolTop** | ATR naik + RSI > 70 | 🔴 DANGER | 🔴 Merah |
| **VolBot** | ATR naik + RSI < 30 | 🔴 DANGER | 🔴 Merah |
| **OB+BB** | RSI overbought + BB High touch | 🔴 DANGER | 🔴 Merah |
| **OS+BB** | RSI oversold + BB Low touch | 🔴 DANGER | 🔴 Merah |
| **~Res** | Harga dekat Resistance + gate bullish | 🟡 CAUTION | 🟡 Orange |
| **~Sup** | Harga dekat Support + gate bearish | 🟡 CAUTION | 🟡 Orange |
| **ATR+** | ATR spike > 1.5x previous | 🟡 CAUTION | 🟡 Orange |
| **NoGAP** | GAP < 5 — signal tidak dihitung | ⚪ INFO | ⚪ Abu |
| *(kosong)* | Tidak ada warning | ✅ AMAN | ⚪ Abu |

### Penjelasan Detail:

#### 🔴 DANGER — Pertimbangkan Tutup Posisi
| Warning | Arti | Aksi |
|---------|------|------|
| **VolTop** | Volatilitas naik + RSI kepanasan | Siap-siap take profit / tight trailing |
| **VolBot** | Volatilitas naik + RSI oversold | Bisa reversal, siap-siap exit |
| **OB+BB** | Konfirmasi ganda bearish reversal | Segitiga api — close SELL |
| **OS+BB** | Konfirmasi ganda bullish reversal | Segitiga api — close BUY |

#### 🟡 CAUTION — Waspada
| Warning | Arti | Aksi |
|---------|------|------|
| **~Res** | Harga < 0.5 ATR dari Resistance | Kalo punya BUY, pertimbangkan TP |
| **~Sup** | Harga < 0.5 ATR dari Support | Kalo punya SELL, pertimbangkan TP |
| **ATR+** | Volatilitas naik > 50% | Spread melebar, hati-hati entry |

---

## 🎯 Ringkasan Scoring

```
GAP ≥ 5 → Boleh lanjut
    ├── 4/4 EMA gate    → +3
    ├── 3/4             → +2
    ├── 2/4             → +1
    │
    ├── BB touch + RSI  → +2
    ├── BB/RSI sendiri  → +1
    │
    ├── Dekat SnR       → +1
    ├── GAP ≥ 7         → +2
    │
    └── EMA lawan GAP   → −2
          ──────────
          ≥ 7  = STRONG
          ≥ 4  = Regular
          < 4  = WAIT
```

---

*Dibuat: 6 Mei 2026 — Callunk & Cuy*
