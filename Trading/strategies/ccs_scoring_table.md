# CCS Scoring Reference — Scoring by Indicator Kombinasi

## Rumus Scoring
```
GAP poin = gap_value - 3    (min 0)
GT poin  = gates: 4/4=+3, 3/4=+2, 2/4=+1
RSI poin = konfirmasi/turning = +1
SnR poin = dekat S/R = +1
ATR poin = Sta=+1, Vol=−1
BB poin  = touch = +1
         − Conflict penalty (−2 jika EMA lawan arah GAP)

≥ 7 = STRONG | ≥ 4 = Regular | < 4 = WAIT
```

---

## 1️⃣ GAP + GT saja (max score = 9)

### BUY side (GAP positif)

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **3/1** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |
| **2/2** | 2 W | 3 W | 4 B | 5 B | 6 B | **7 SB** |
| **1/3** | 1 W | 2 W | 3 W | 4 B | 5 B | 6 B |
| **0/4** | 0 W | 1 W | 2 W | 3 W | 4 B | 5 B |
> Angka = score total. W=Wait, B=Buy, SB=Strong Buy.

### SELL side (GAP negatif)

| GT ↓ GAP→ | −4.0 | −5.0 | −6.0 | −7.0 | −8.0 | −9.0 |
|----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 0 W | 1 W | 2 W | 3 W | 4 S | 5 S |
| **3/1** | 1 W | 2 W | 3 W | 4 S | 5 S | 6 S |
| **2/2** | 2 W | 3 W | 4 S | 5 S | 6 S | **7 SS** |
| **1/3** | 3 W | 4 S | 5 S | 6 S | **7 SS** | **8 SS** |
| **0/4** | 4 S | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** |
> S=Sell, SS=Strong Sell.

---

## 2️⃣ GAP + GT + RSI (max score = 10)

### BUY side

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | **5 B** | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **3/1** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **2/2** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |
| **1/3** | 2 W | 3 W | 4 B | 5 B | 6 B | **7 SB** |
| **0/4** | 1 W | 2 W | 3 W | 4 B | 5 B | 6 B |

### SELL side

| GT ↓ GAP→ | −4.0 | −5.0 | −6.0 | −7.0 | −8.0 | −9.0 |
|----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 1 W | 2 W | 3 W | 4 S | 5 S | 6 S |
| **3/1** | 2 W | 3 W | 4 S | 5 S | 6 S | **7 SS** |
| **2/2** | 3 W | 4 S | 5 S | 6 S | **7 SS** | **8 SS** |
| **1/3** | 4 S | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** |
| **0/4** | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** |

> RSI +1 nyalakan (toggle ON). Tanpa RSI → sama seperti Combo 1.

---

## 3️⃣ GAP + GT + RSI + SnR (max score = 11)

### BUY side

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** |
| **3/1** | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **2/2** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **1/3** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |
| **0/4** | 2 W | 3 W | 4 B | 5 B | 6 B | **7 SB** |

### SELL side

| GT ↓ GAP→ | −4.0 | −5.0 | −6.0 | −7.0 | −8.0 | −9.0 |
|----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 2 W | 3 W | 4 S | 5 S | 6 S | **7 SS** |
| **3/1** | 3 W | 4 S | 5 S | 6 S | **7 SS** | **8 SS** |
| **2/2** | 4 S | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** |
| **1/3** | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** |
| **0/4** | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** | **11 SS** |

> SnR +1 (+1 jika dekat S/R). SnR toggle ON.

---

## 4️⃣ GAP + GT + RSI + SnR + ATR (max score = +12 / −12)

ATR modifier: Sta=+1, Vol=−1.

### BUY — ATR = Sta (+1)

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** | **12 SB** |
| **3/1** | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** |
| **2/2** | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **1/3** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **0/4** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |

### BUY — ATR = Vol (−1)

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **3/1** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **2/2** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |
| **1/3** | 2 W | 3 W | 4 B | 5 B | 6 B | **7 SB** |
| **0/4** | 1 W | 2 W | 3 W | 4 B | 5 B | 6 B |

### SELL — ATR = Sta (+1)

| GT ↓ GAP→ | −4.0 | −5.0 | −6.0 | −7.0 | −8.0 | −9.0 |
|----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 3 W | 4 S | 5 S | 6 S | **7 SS** | **8 SS** |
| **3/1** | 4 S | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** |
| **2/2** | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** |
| **1/3** | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** | **11 SS** |
| **0/4** | **7 SS** | **8 SS** | **9 SS** | **10 SS** | **11 SS** | **12 SS** |

---

## 5️⃣ GAP + GT + RSI + SnR + ATR + BB (max score = +13 / −13)

BB memberikan +1 saat touch. ATAU bisa −1 kalo Volatile.

### BUY — ATR Sta + BB touch

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | **8 SB** | **9 SB** | **10 SB** | **11 SB** | **12 SB** | **13 SB** |
| **3/1** | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** | **12 SB** |
| **2/2** | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** |
| **1/3** | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **0/4** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |

### BUY — ATR Vol, BB touch

| GT ↓ GAP→ | 4.0 | 5.0 | 6.0 | 7.0 | 8.0 | 9.0 |
|-----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** | **11 SB** |
| **3/1** | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** | **10 SB** |
| **2/2** | 4 B | 5 B | 6 B | **7 SB** | **8 SB** | **9 SB** |
| **1/3** | 3 W | 4 B | 5 B | 6 B | **7 SB** | **8 SB** |
| **0/4** | 2 W | 3 W | 4 B | 5 B | 6 B | **7 SB** |

### SELL — ATR Sta + BB touch

| GT ↓ GAP→ | −4.0 | −5.0 | −6.0 | −7.0 | −8.0 | −9.0 |
|----------|---:|----:|----:|----:|----:|----:|
| **4/0** | 4 S | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** |
| **3/1** | 5 S | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** |
| **2/2** | 6 S | **7 SS** | **8 SS** | **9 SS** | **10 SS** | **11 SS** |
| **1/3** | **7 SS** | **8 SS** | **9 SS** | **10 SS** | **11 SS** | **12 SS** |
| **0/4** | **8 SS** | **9 SS** | **10 SS** | **11 SS** | **12 SS** | **13 SS** |

---

## Ringkasan — Minimum GAP untuk Signal

Berapa GAP minimal yang diperlukan untuk mencapai signal tertentu?

### STRONG BUY (score ≥ 7)

| Kombinasi | GAP minimal jika GT=4/0 | GAP minimal jika GT=3/1 | GAP minimal jika GT=2/2 |
|-----------|:-----------------------:|:-----------------------:|:-----------------------:|
| GAP+GT | **7.0** | **8.0** | **9.0** |
| +RSI | 6.0 | **7.0** | **8.0** |
| +SnR | 5.0 | 6.0 | **7.0** |
| +ATR Sta | 4.0 | 5.0 | 6.0 |
| +ATR Vol+BB | 5.0 | 6.0 | **7.0** |

### BUY (score ≥ 4)

| Kombinasi | GAP minimal jika GT=4/0 | GAP minimal jika GT=3/1 | GAP minimal jika GT=2/2 |
|-----------|:-----------------------:|:-----------------------:|:-----------------------:|
| GAP+GT | **4.0** | **5.0** | **6.0** |
| +RSI | 4.0 | 4.0 | **5.0** |
| +SnR | 4.0 | 4.0 | **4.0** |
| +ATR Sta | 4.0 | 4.0 | **4.0** |
| +ATR Vol+BB | 4.0 | **5.0** | **6.0** |

---

## Cara Baca

1. Cari baris dengan GT yang sesuai (4/0, 3/1, dst)
2. Cari kolom GAP yang sesuai (4.0-9.0)
3. Lihat score + signal di intersection
4. W = Wait, B = Buy, SB = Strong Buy, S = Sell, SS = Strong Sell

Contoh: GAP=5.0 + GT=3/1 → dengan combo 1 (GAP+GT saja) dapat score 4 → **BUY** ✅
Dengan combo 5 (semua ON) + ATR Sta + BB touch → score 4+1+1+1 = **7 → STRONG BUY** 🔥

