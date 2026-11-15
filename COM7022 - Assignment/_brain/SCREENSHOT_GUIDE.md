# راهنمای گرفتن و جایگزینی اسکرین‌شات‌های کد (دستی)

تمام اسکرین‌شات‌های کد در گزارش فعلاً **تصویرِ رندرشده** از متن نوت‌بوک هستند، نه اسکرین‌شات واقعی از اجرای تو.
این فایل مشخص می‌کند هر اسکرین‌شات از کدام سلول گرفته شود، با چه نامی ذخیره شود و کجای گزارش می‌نشیند.

> [!IMPORTANT]
> اسکریپت `build_report.py` دیگر به‌صورت پیش‌فرض اسکرین‌شات‌ها را بازسازی **نمی‌کند**، پس فایل‌هایی که خودت جایگزین کنی پاک نمی‌شوند.
> هرگز `python build_report.py shots` را اجرا نکن، مگر بخواهی اسکرین‌شات‌های دستی‌ات با تصاویر رندرشده بازنویسی شوند.

---

## مرحله ۱ — اجرای نوت‌بوک توسط خودت

1. فایل `COM7022 - Assignment/COM7022_Clustering_25199053.ipynb` را در **Google Colab** باز کن
   (یا از لینک گیت‌هاب: `https://github.com/kvmmn/_COM7022_MachineLearning` → فایل نوت‌بوک → دکمه Open in Colab).
2. فایل داده `Sales-[5444].csv` را در پنل Files آپلود کن (کنار نوت‌بوک).
3. `Runtime → Restart session and run all` را بزن تا همه سلول‌ها از صفر اجرا شوند.
4. بررسی کن که اعداد کلیدی همان‌هایی باشند که در گزارش آمده (seed = 274):
   - K-Means، k = 4 → silhouette **0.307**، Davies-Bouldin **1.013**
   - Bootstrap ARI → **0.929**
   - PCA → **78.7%** واریانس در دو مؤلفه اول
   - سهم Cluster 2 → **90.7%** از کل فروش
   اگر عددی متفاوت بود، قبل از ادامه به من بگو؛ گزارش باید با اجرای تو یکی باشد.

## مرحله ۲ — قواعد گرفتن اسکرین‌شات

- **کل سلول** را بگیر: هم کد و هم خروجی زیرش (اگر خروجی دارد). شماره سلول/`[ ]` اجرا باید دیده شود.
- اگر سلول بلند است و در یک صفحه جا نمی‌شود، دو اسکرین‌شات بگیر و با پسوند `_a` و `_b` ذخیره کن
  (مثلاً `cell13_a.png`، `cell13_b.png`) و به من بگو تا گزارش را برای دو تصویر تنظیم کنم.
- زوم مرورگر را روی ۱۰۰٪ یا ۱۱۰٪ بگذار و پهنای پنجره را ثابت نگه دار تا همه تصاویر هم‌اندازه باشند.
- تم روشن (Light) Colab خواناتر چاپ می‌شود.
- فرمت **PNG**، و نام فایل **دقیقاً** همان نامی باشد که در جدول‌های زیر آمده (حروف کوچک).
- در مک: `Cmd + Shift + 4` و انتخاب ناحیه؛ یا `Cmd + Shift + 4` سپس `Space` برای گرفتن یک پنجره.

---

## مرحله ۳ — اسکرین‌شات‌های متن اصلی گزارش (۷ عدد)

پوشه مقصد: `COM7022 - Assignment/output/screenshots/`

| شکل در گزارش | نام فایل | سلول نوت‌بوک | خط اول سلول (برای پیدا کردن) |
|---|---|---|---|
| Figure 5 — Missing-value and duplicate audit | `code02_missing_values.png` | code cell 5 | `# Missing values per column, as counts and percentages` |
| Figure 6 — Recovery of price / currency conversion | `code03_price_recovery.png` | code cell 11 | `df = raw.copy()` |
| Figure 7 — Recovery of units sold | `code04_sold_recovery.png` | code cell 12 | `# 3.3 Units sold: recover from the 'text' column` |
| Figure 8 — Stock reconstruction and censoring | `code05_stock_level.png` | code cell 13 | `# 3.4 Stock level: rebuild it from the listing wording` |
| Figure 9 — Normalisation of category labels | `code06_product_type.png` | code cell 14 | `# 3.5 Product type: collapse the messy category labels` |
| Figure 11 — Log transformation | `code07_log_transform.png` | code cell 15 | `# 3.10 Transform the skewed measures` |
| Figure 12 — Z-score standardisation | `code08_scaling.png` | code cell 20 | `FEATURES = ["log_price", "log_sold", "stock_level"]` |

> این فایل‌ها در پوشه هستند ولی در گزارش استفاده **نمی‌شوند** و نیازی به جایگزینی ندارند:
> `code01_import_data`، `code09_pca`، `code10_kmeans_scan`، `code11_hierarchical`، `code12_dbscan_kdist`، `code13_metrics`، `code14_stability`.

---

## مرحله ۴ — اسکرین‌شات‌های پیوست A (۵۴ عدد، یکی برای هر سلول کد)

پوشه مقصد: `COM7022 - Assignment/output/screenshots/appendix/`
شماره‌گذاری فقط سلول‌های **کد** را می‌شمارد (سلول‌های متنی/Markdown شمرده نمی‌شوند).
اگر Colab سلول اضافه‌ای (مثل نشان Open in Colab) بالای نوت‌بوک گذاشت، آن را نشمار؛ از روی «خط اول» تطبیق بده.

| کد در پیوست | نام فایل | بخش نوت‌بوک | خط اول سلول |
|---|---|---|---|
| A1 | `cell01.png` | 0. Set-up | `# Standard libraries` |
| A2 | `cell02.png` | 0. Set-up | `# Type: the print figures use Carlito…` |
| A3 | `cell03.png` | 1. Data import | `DATA_FILE = "Sales-[5444].csv"` |
| A4 | `cell04.png` | 1. Data import | `# Column types and non-null counts` |
| A5 | `cell05.png` | 2. Descriptive statistics | `# Missing values per column…` |
| A6 | `cell06.png` | 2. Descriptive statistics | `# Figure 1: where the gaps are` |
| A7 | `cell07.png` | 2. Descriptive statistics | `# Descriptive statistics for the numeric columns…` |
| A8 | `cell08.png` | 2. Descriptive statistics | `# Text and category columns…` |
| A9 | `cell09.png` | 2. Descriptive statistics | `# The 'text' column holds the availability…` |
| A10 | `cell10.png` | 2. Descriptive statistics | `# Figure 2: raw distributions of price and units sold` |
| A11 | `cell11.png` | 3. Pre-processing | `df = raw.copy()` |
| A12 | `cell12.png` | 3. Pre-processing | `# 3.3 Units sold…` |
| A13 | `cell13.png` | 3. Pre-processing | `# 3.4 Stock level…` |
| A14 | `cell14.png` | 3. Pre-processing | `# 3.5 Product type…` |
| A15 | `cell15.png` | 3. Pre-processing | `# 3.10 Transform the skewed measures…` |
| A16 | `cell16.png` | 3. Pre-processing | `# Figure 3: distributions after the log transform` |
| A17 | `cell17.png` | 3. Pre-processing | `# Descriptive statistics after cleaning…` |
| A18 | `cell18.png` | 4. Feature selection | `candidates = ["log_price", "log_sold", …` |
| A19 | `cell19.png` | 4. Feature selection | `# Compare feature sets on the same footing…` |
| A20 | `cell20.png` | 4. Feature selection | `FEATURES = ["log_price", "log_sold", "stock_level"]` |
| A21 | `cell21.png` | 5. PCA | `pca = PCA(random_state=SEED)` |
| A22 | `cell22.png` | 5. PCA | `# Figure 5: explained variance…` |
| A23 | `cell23.png` | 6. K-Means | `k_values = range(2, 11)` |
| A24 | `cell24.png` | 6. K-Means | `K_FINAL = 4` |
| A25 | `cell25.png` | 6. K-Means | `# Figure 6: elbow (inertia) and silhouette against k` |
| A26 | `cell26.png` | 6. K-Means | `kmeans = KMeans(n_clusters=K_FINAL, …` |
| A27 | `cell27.png` | 6. K-Means | `# Figure 7: K-Means clusters on the PCA plane…` |
| A28 | `cell28.png` | 7. Hierarchical | `linkage_methods = ["single", "complete", …` |
| A29 | `cell29.png` | 7. Hierarchical | `# Figure 8: dendrograms for the four linkages…` |
| A30 | `cell30.png` | 7. Hierarchical | `# Ward: metrics across k…` |
| A31 | `cell31.png` | 7. Hierarchical | `# Figure 9: Ward dendrogram with the cut…` |
| A32 | `cell32.png` | 8. DBSCAN | `MIN_SAMPLES = 2 * len(FEATURES)` |
| A33 | `cell33.png` | 8. DBSCAN | `# Grid search over eps and min_samples…` |
| A34 | `cell34.png` | 8. DBSCAN | `dbscan_grid.pivot(index="eps", …` |
| A35 | `cell35.png` | 8. DBSCAN | `EPS_FINAL = 0.45` |
| A36 | `cell36.png` | 8. DBSCAN | `# Figure 11: DBSCAN result on the PCA plane` |
| A37 | `cell37.png` | 9. HDBSCAN | `# Grid over both settings…` |
| A38 | `cell38.png` | 9. HDBSCAN | `MIN_CLUSTER_SIZE = 30 …` |
| A39 | `cell39.png` | 9. HDBSCAN | `# Robustness: is the result produced by ties…` |
| A40 | `cell40.png` | 9. HDBSCAN | `# Figure 18: HDBSCAN on the PCA plane…` |
| A41 | `cell41.png` | 10. Model comparison | `def internal_scores(labels, ignore_noise=False):` |
| A42 | `cell42.png` | 10. Model comparison | `# Seed stability for K-Means…` |
| A43 | `cell43.png` | 10. Model comparison | `# Figure 12: side-by-side comparison of the models` |
| A44 | `cell44.png` | 11. Final model | `FINAL = "kmeans"` |
| A45 | `cell45.png` | 11. Final model | `# Product-type mix per cluster…` |
| A46 | `cell46.png` | 11. Final model | `# Figure 13: cluster profiles…` |
| A47 | `cell47.png` | 11. Final model | `# Figure 14: distributions of price, units sold and stock…` |
| A48 | `cell48.png` | 12. Segment rules | `from sklearn.tree import DecisionTreeClassifier, …` |
| A49 | `cell49.png` | 12. Segment rules | `# One line for the most valuable segment…` |
| A50 | `cell50.png` | 13. Report diagrams | `from matplotlib.patches import FancyBboxPatch` |
| A51 | `cell51.png` | 13. Report diagrams | `# Figure 15: the workflow…` |
| A52 | `cell52.png` | 13. Report diagrams | `# Figure 16: data-preparation flow…` |
| A53 | `cell53.png` | 13. Report diagrams | `# Figure 17: share of listings vs share of units sold…` |
| A54 | `cell54.png` | 13. Report diagrams | `# Save the frozen results ledger…` |

> نکته: تمام 54 سلول کد بدون نیاز به دانلود مدل‌های سنگین و معمولاً در کمتر از 10 ثانیه اجرا می‌شوند؛ بعد از اتمام `Runtime -> Run all` خروجی‌ها کامل آماده است و می‌توانی عکس بگیری.

---

## مرحله ۵ — ساخت دوباره گزارش

دو راه داری:

**راه الف (توصیه‌شده — خودکار):** فایل‌ها را با همان نام‌ها در پوشه‌های بالا جایگزین کن، Word را ببند، و اجرا کن:

```bash
cd "/Users/kaveh/Desktop/base/_LIBRARY/_MASTER/_COM7022_Machine_Learning"
.venv/bin/python "COM7022 - Assignment/scripts/build_report.py"
```

این فقط `docx` (Word و PDF) و `html` (صفحه گیت‌هاب) را می‌سازد و به اسکرین‌شات‌ها دست نمی‌زند.
(پیش‌نیاز: `python-docx` در `.venv` و LibreOffice روی سیستم.)

**راه ب (کاملاً دستی در Word):** فایل `COM7022_Portfolio_25199053_final.docx` را باز کن، روی هر تصویر کد
راست‌کلیک → **Change Picture → From a File** و فایل خودت را انتخاب کن؛ کپشن و مسیر زیر تصویر دست نمی‌خورد.
در پایان `File → Save As → PDF`.
عیب این راه: صفحه گیت‌هاب (`index.html`) به‌روز نمی‌شود، مگر بعداً راه الف را هم اجرا کنی.

## مرحله ۶ — بررسی نهایی

- [ ] هر ۷ اسکرین‌شات متن اصلی و هر ۵۷ اسکرین‌شات پیوست جایگزین شده‌اند.
- [ ] شماره‌های داخل اسکرین‌شات‌ها (خروجی سلول‌ها) با جدول‌ها و متن گزارش یکی هستند.
- [ ] هیچ اسکرین‌شاتی بریده یا ناخوانا نیست.
- [ ] نوت‌بوک اجراشده را هم در Colab ذخیره کن (`File → Save a copy in GitHub`) تا نسخه گیت‌هاب با اسکرین‌شات‌ها یکی باشد.
