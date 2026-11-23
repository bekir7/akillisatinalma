# Akıllı Satın Alma — Tedarikçi Teklif Karşılaştırma

Satın alma ekiplerinin en çok vakit kaybettiği işlerden biri: farklı tedarikçilerden gelen **farklı formatlardaki** teklifleri tek tek açıp Excel’de birleştirmek, fiyat / teslim / vade karşılaştırmak ve yöneticiye özet çıkarmak.

Bu proje tam olarak bunu otomatikleştirir.

| | |
|---|---|
| **Dil** | Python 3.10+ |
| **Girdi** | CSV, Excel (`.xlsx`), PDF |
| **Çıktı** | Konsol özeti + Excel yönetici raporu |
| **Amaç** | Portföy / iş süreci otomasyonu örneği (model eğitmek değil) |

---

## İçindekiler

1. [Ne yapar?](#ne-yapar)
2. [Nasıl çalışır? (akış)](#nasıl-çalışır-akış)
3. [Gereksinimler](#gereksinimler)
4. [Kurulum](#kurulum)
5. [Hızlı başlangıç (örnek veriyle)](#hızlı-başlangıç-örnek-veriyle)
6. [Kullanım](#kullanım)
7. [Kendi teklif dosyalarınızı ekleme](#kendi-teklif-dosyalarınızı-ekleme)
8. [Skorlama mantığı](#skorlama-mantığı)
9. [Excel rapor içeriği](#excel-rapor-içeriği)
10. [Proje yapısı](#proje-yapısı)
11. [Sık karşılaşılan sorunlar](#sık-karşılaşılan-sorunlar)
12. [İleride eklenebilecekler](#ileride-eklenebilecekler)
13. [Lisans](#lisans)

---

## Ne yapar?

Script şunları yapar:

1. `data/quotes/` klasöründeki tüm teklif dosyalarını tarar  
2. Her dosyayı okur (CSV / Excel / PDF)  
3. Farklı sütun adlarını ve sayı formatlarını **ortak bir modele** çevirir  
4. Aynı ürün koduna ait teklifleri gruplar  
5. **Birim fiyat + teslim süresi + ödeme vadesi** ile skor hesaplar  
6. Her ürün için **en uygun tedarikçiyi önerir**  
7. Yöneticiye hem konsolda hem Excel’de özet rapor üretir  

### Çözdüğü gerçek problem

Tedarikçi A CSV gönderir (`Ürün Kodu`, `Birim Fiyat`, `30 gün`),  
Tedarikçi B Excel gönderir (`SKU`, `Unit Price`, `Net 60`),  
Tedarikçi C PDF gönderir…  

Manuel karşılaştırma yavaş ve hataya açık. Bu araç format farkını otomatik toplar.

---

## Nasıl çalışır? (akış)

```
data/quotes/*.csv|xlsx|pdf
        │
        ▼
   readers.py          → ham tabloyu oku
        │
        ▼
   normalize.py        → sütun eşle, fiyat/vade parse et, kur çevir (TRY)
        │
        ▼
   scoring.py          → ürün bazlı ağırlıklı skor
        │
        ▼
   report.py + konsol  → yönetici özeti + Excel
```

**Önemli noktalar:**

- Sütun adları esnek eşlenir (`Ürün Kodu` ≈ `SKU` ≈ `Stok Kodu`)
- Türkçe sayı formatı desteklenir (`4.850,00` → `4850.00`, `5.100` → `5100`)
- Vade metinleri çözülür (`Peşin` → 0, `Net 60` → 60, `45 gün` → 45)
- EUR/USD gibi dövizler demo kur ile TRY’ye çevrilir (karşılaştırma aynı birimde olsun diye)

---

## Gereksinimler

- Windows / macOS / Linux
- **Python 3.10 veya üzeri** (geliştirme Python 3.12 ile yapıldı)
- İnternet (ilk kurulumda paket indirme)

Bağımlılıklar `requirements.txt` içinde:

- `pandas` — tablo işleme
- `openpyxl` — Excel okuma/yazma
- `pdfplumber` — PDF tablo çıkarma
- `reportlab` — örnek PDF üretme (sadece demo veri için)

---

## Kurulum

### 1) Projeyi açın

```powershell
cd C:\Users\user\Desktop\akillisatinalma
```

### 2) Sanal ortam oluşturun

```powershell
python -m venv .venv
```

### 3) Sanal ortamı etkinleştirin

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\activate
```

**Windows (CMD):**

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Başarılı olursa terminal satırının başında `(.venv)` görünür.

### 4) Paketleri kurun

```powershell
pip install -r requirements.txt
```

> Not: Projede zaten `.venv` kurulmuş olabilir. O durumda sadece activate + gerekirse `pip install` yeterlidir.

---

## Hızlı başlangıç (örnek veriyle)

Örnek teklifleri oluşturup karşılaştırmayı çalıştırın:

```powershell
python scripts\generate_samples.py
python main.py
```

Beklenen sonuç:

- Terminalde ürün bazlı öneri listesi
- `output\tedarikci_karsilastirma_raporu.xlsx` dosyası

### Örnek girdi dosyaları

`scripts/generate_samples.py` şunları üretir:

| Dosya | Format | Tedarikçi | Özellik |
|-------|--------|-----------|---------|
| `anadolu_fan_teklif.csv` | CSV (`;`) | Anadolu Fan A.Ş. | Türkçe sütun adları |
| `euroagri_quote.xlsx` | Excel | EuroAgri GmbH | İngilizce sütunlar, EUR fiyat |
| `ege_kanatli_fiyat.csv` | CSV (`,`) | Ege Kanatlı Ekipman | Farklı TR sütun isimleri |
| `delta_otomasyon_teklif.pdf` | PDF | Delta Otomasyon | Tablo içeren PDF |

Bu çeşitlilik bilerek var: gerçek hayatta her tedarikçi farklı şablon kullanır.

---

## Kullanım

### Temel çalıştırma

```powershell
python main.py
```

Varsayılanlar:

- Girdi klasörü: `data/quotes`
- Çıktı dosyası: `output/tedarikci_karsilastirma_raporu.xlsx`
- Ağırlıklar: fiyat %50, teslim %30, vade %20

### Parametreler

```powershell
python main.py --help
```

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `--input` | Teklif klasörü | `data/quotes` |
| `--output` | Excel çıktı yolu | `output/tedarikci_karsilastirma_raporu.xlsx` |
| `--price-weight` | Fiyat ağırlığı | `0.50` |
| `--delivery-weight` | Teslim ağırlığı | `0.30` |
| `--payment-weight` | Vade ağırlığı | `0.20` |

### Örnekler

Fiyatı daha önemli yap:

```powershell
python main.py --price-weight 0.7 --delivery-weight 0.2 --payment-weight 0.1
```

Başka klasörden oku, başka yere yaz:

```powershell
python main.py --input data\quotes --output output\rapor_2026-11-23.xlsx
```

Ağırlık toplamı 1 değilse script otomatik normalize eder (uyarı basar).

---

## Kendi teklif dosyalarınızı ekleme

1. Teklif dosyanızı `data\quotes\` içine kopyalayın (`.csv`, `.xlsx`, `.pdf`)
2. `python main.py` çalıştırın

### Desteklenen alanlar

Script şu alanları arar (isimler esnek):

| Alan | Örnek sütun adları | Zorunlu mu? |
|------|--------------------|-------------|
| Tedarikçi | `Tedarikçi`, `Firma`, `Vendor`, `Supplier` | Evet* |
| Ürün kodu | `Ürün Kodu`, `SKU`, `Stok Kodu`, `Kod` | Evet |
| Ürün adı | `Ürün Adı`, `Malzeme`, `Description` | Hayır |
| Birim fiyat | `Birim Fiyat`, `Unit Price`, `Net Fiyat` | Evet |
| Para birimi | `Para Birimi`, `Currency`, `PB` | Hayır (varsayılan TRY) |
| Teslim süresi | `Teslim Süresi`, `Lead Time`, `Teslimat` | Hayır (varsayılan 30) |
| Ödeme vadesi | `Ödeme Vadesi`, `Payment Terms`, `Vade` | Hayır (varsayılan 0) |
| Miktar | `Miktar`, `Qty`, `Adet` | Hayır (varsayılan 1) |

\* Dosya adından da tedarikçi tahmin edilir (`anadolu_fan_teklif.csv` → `Anadolu Fan`).

### İpuçları

- Aynı ürünleri karşılaştırmak için **ürün kodları aynı** olmalı (`FAN-220` gibi)
- CSV’de `;` veya `,` ayırıcı kullanılabilir
- PDF’de mümkünse **tablo** olsun (serbest metin de kısmen desteklenir)
- Karışık döviz varsa fiyatlar demo kur ile TRY’ye çevrilir:
  - EUR = 38.5
  - USD = 35.0
  - GBP = 44.0  
  (`src/normalize.py` içindeki `FX_TO_TRY` sözlüğünden değiştirilebilir)

---

## Skorlama mantığı

Her ürün için aday tedarikçiler 0–1 arası skorlanır, sonra ağırlıklı toplanır:

```
Toplam Skor =
  (Fiyat Skoru  × price_weight) +
  (Teslim Skoru × delivery_weight) +
  (Vade Skoru   × payment_weight)
```

| Kriter | Tercih | Açıklama |
|--------|--------|----------|
| Fiyat | Düşük daha iyi | En ucuz = 1, en pahalı = 0 |
| Teslim | Kısa daha iyi | En hızlı = 1, en geç = 0 |
| Vade | Uzun daha iyi | En uzun vade = 1 (nakit akışı avantajı) |

En yüksek toplam skoru alan tedarikçi **önerilir** (`★`).

> Bu bir karar destek aracıdır. Kalite, risk, geçmiş performans gibi kriterler henüz modele dahil değildir; nihai sipariş kararı satın alma / yönetimde kalmalıdır.

---

## Excel rapor içeriği

Dosya: `output/tedarikci_karsilastirma_raporu.xlsx`

| Sayfa | İçerik |
|-------|--------|
| `Yonetici_Ozet` | Tarih, satır sayısı, ağırlıklar, tahmini tasarruf + öneri tablosu |
| `Oneriler` | Ürün bazında önerilen tedarikçi özeti |
| `Detayli_Karsilastirma` | Tüm adaylar, alt skorlar, toplam skor, `Öneri=EVET` |
| `Ham_Veri` | Normalize edilmiş ham teklif satırları |

Konsolda da aynı önerilerin kısa özeti basılır.

---

## Proje yapısı

```
akillisatinalma/
├── main.py                      # CLI giriş noktası
├── requirements.txt             # Python bağımlılıkları
├── README.md
├── .gitignore
├── data/
│   └── quotes/                  # Girdi teklif dosyaları
├── output/
│   └── tedarikci_karsilastirma_raporu.xlsx
├── scripts/
│   └── generate_samples.py      # Demo CSV/Excel/PDF üretici
└── src/
    ├── models.py                # QuoteLine, skor veri modelleri
    ├── readers.py               # Dosya okuma (CSV/Excel/PDF)
    ├── normalize.py             # Sütun alias + tip/kur dönüşümü
    ├── scoring.py               # Ağırlıklı karşılaştırma
    ├── report.py                # Excel + konsol rapor
    └── pipeline.py              # Uçtan uca orkestrasyon
```

---

## Sık karşılaşılan sorunlar

### `python` tanınmıyor

Python PATH’e ekli olmayabilir. Şunu deneyin:

```powershell
py -3 -m venv .venv
py -3 main.py
```

### `ModuleNotFoundError: pandas` / `pdfplumber`

Sanal ortam aktif değil veya paketler kurulmamış:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### `Teklif dosyası bulunamadı`

`data/quotes` boş. Önce örnek üretin:

```powershell
python scripts\generate_samples.py
```

veya kendi dosyalarınızı bu klasöre koyun.

### PDF’den veri çıkmıyor

- PDF taranmış görüntü (scan) ise tablo çıkmayabilir; metin/tablo içeren PDF kullanın
- Gerekirse aynı veriyi CSV/Excel olarak koyun

### Fiyatlar yanlış görünüyor

- Türkçe binlik/ondalık (`1.250,50` vs `1,250.50`) karışmış olabilir
- Dövizli tekliflerde `FX_TO_TRY` kurlarını güncelleyin

### Excel dosyası açıkken yazılamıyor

Rapor açıksa Excel kilidi nedeniyle hata alabilirsiniz. Dosyayı kapatıp tekrar çalıştırın.

---

## İleride eklenebilecekler

Bu proje bilinçli olarak “çalışan, pratik otomasyon” odaklıdır. Kolay genişletmeler:

- **n8n / Power Automate / Make:** Outlook’a gelen teklif eklerini `data/quotes`’a kaydedip scripti tetiklemek
- **CANIAS ERP entegrasyonu:** önerilen satırları sipariş taslağı olarak yazmak
- **LLM / AI Agent:** serbest metin PDF’lerden alan çıkarma, yöneticiye doğal dil özet
- **Ek skor kriterleri:** kalite puanı, tedarikçi risk skoru, minimum sipariş miktarı
- **Canlı kur servisi:** TCMB / ERP kur endpoint’i

---

## Lisans

MIT

---

## Kısa özet (başvuru / GitHub için)

> Python ile CSV/Excel/PDF tedarikçi tekliflerini okuyan, format farklarını normalize eden, fiyat–teslim–vade skoruna göre en uygun tedarikçiyi öneren ve yönetici Excel raporu üreten satın alma otomasyonu.
