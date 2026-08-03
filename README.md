# Görsel Format Dönüştürücü (Windows Sağ Tık)

Explorer'da seçili görselleri yerel olarak [Pillow](https://pillow.readthedocs.io/) ile dönüştürür; çıktıyı aynı dizindeki `converted` klasörüne yazar.

TinyPNG sıkıştırma aracından (`tiny_func`) bağımsızdır; menü ve kurulum ayrıdır.

## Özellikler

- Bir veya birden fazla görsel seçimi
- Sağ tık menüsü: **Formata dönüştür** → seçim penceresi
- Üstte **Hepsini aynı formata çevir** (tek format) veya dosya başına ayrı format
- Format seçilmeden **Tamam** kullanılamaz
- Desteklenen: `.png`, `.jpg`/`.jpeg`, `.webp`, `.avif`
- Aynı formata da yazar
- Çıktı: `<görselin-dizini>/converted/` (klasör varsa yeniden kullanılır)
- İsim çakışmasında `photo.png` → `photo_1.png` → `photo_2.png` …
- Tek dosya hatasında işlem diğer dosyalar için devam eder
- API yok; tamamen yerel

## Gereksinimler

- Windows 10/11
- Python 3.10+ (tkinter ile birlikte; standart Windows kurulumunda gelir)

## Kurulum

1. Bu klasörde sanal ortam ve bağımlılıkları kurun:

```powershell
cd C:\Users\emink\Documents\file_conv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Sağ tık menüsünü kaydedin (yönetici gerekmez):

```powershell
powershell -ExecutionPolicy Bypass -File .\install_context_menu.ps1
```

3. Explorer'ı yenileyin (görev yöneticisinden Windows Explorer'ı yeniden başlatın veya bir kez oturumu kapatıp açın).

## Kullanım

1. Explorer'da bir veya daha fazla desteklenen görsel seçin.
2. Sağ tık → **Formata dönüştür**.
3. Açılan pencerede:
   - **Hepsini aynı formata çevir** işaretliyse üstten tek format seçin.
   - İşaretli değilse her satırda ayrı format seçin.
4. **Tamam** ile dönüştürün; dosyalar `converted` klasörüne yazılır.

Komut satırından:

```powershell
.\convert.bat "C:\yol\photo.webp" "C:\yol\other.jpg"
```

## Kaldırma

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_context_menu.ps1
```

Yalnızca bu aracın menü kaydını siler; TinyPNG menüsüne dokunmaz.

## Notlar

- Registry kayıtları yalnızca mevcut kullanıcıya (`HKCU`) yazılır.
- Proje klasöründe `.venv` varsa `convert.bat` `pythonw` ile konsolsuz pencere açar.
- JPEG çıktıda şeffaflık beyaz zemine düzleştirilir; PNG / WebP / AVIF şeffaflığı korur.
- JPEG / WebP / AVIF yazarken kalite, mümkünse kaynak boyuttan küçük olacak şekilde ayarlanır.
- PNG kayıpsızdır; özellikle JPEG/WebP → PNG dönüşümünde dosya büyüyebilir.
