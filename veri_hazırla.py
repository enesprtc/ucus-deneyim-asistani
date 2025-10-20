# Gerekli kütüphaneyi içeri aktarıyorum: pandas
# pandas'ı 'pd' kısaltmasıyla kullanacağım. Bu kütüphane, CSV gibi tablolu verileri
# okumak, işlemek ve analiz etmek için çok kullanışlı.
import pandas as pd

# --- Dosya İsimleri Tanımlamaları ---
# Ham veriyi içeren orijinal CSV dosyamın adı.
# Bu dosyanın, bu script ile aynı klasörde olması gerekiyor.
input_filename = "Airline_review.csv" 
# Temizlenmiş ve işlenmiş veriyi kaydedeceğim yeni CSV dosyasının adı.
output_filename = "temiz_havayolu_yorumlari.csv"

# Kullanıcıya hangi dosyanın okunduğunu bildiren bir mesaj yazdırıyorum.
print(f"'{input_filename}' dosyası okunuyor...")

# --- Veri Okuma ve İşleme Bloğu ---
# Kodun bu kısmında hata oluşma ihtimaline karşı bir try-except bloğu kullanıyorum.
# Bu, dosya bulunamazsa veya başka bir sorun çıkarsa programın çökmesini engeller.
try:
    # pandas'ın read_csv fonksiyonu ile ham CSV dosyasını okuyorum.
    # Okunan veriyi 'df' adında bir DataFrame (veri çerçevesi) nesnesine atıyorum.
    # DataFrame, Excel tablosu gibi satır ve sütunlardan oluşan bir yapıdır.
    df = pd.read_csv(input_filename)

    # Verinin başarıyla okunduğunu kullanıcıya bildiriyorum.
    print("Veri başarıyla okundu. Veri temizleme ve birleştirme işlemi başlıyor...")

    # --- Adım 1: Gerekli Sütunları Seçme ---
    # Orijinal CSV'deki tüm sütunlara ihtiyacım yok.
    # Projem için sadece havayolu adı, yorum başlığı ve ana yorum metni önemli.
    # Bu sütunların isimlerini bir liste olarak tanımlıyorum.
    gerekli_sutunlar = ['Airline Name', 'Review_Title', 'Review']
    # DataFrame'den sadece bu sütunları içeren yeni bir DataFrame ('df_temiz') oluşturuyorum.
    # .copy() metodu, orijinal veriyi etkilememek için önemlidir.
    df_temiz = df[gerekli_sutunlar].copy()
    # Kullanıcıya hangi sütunların tutulduğunu bildiriyorum.
    print("- Sadece 'Airline Name', 'Review_Title', 'Review' sütunları tutuldu.")

    # --- Adım 2: Eksik Verileri Temizleme ---
    # Bazen yorum başlığı ('Review_Title') veya yorum metni ('Review') boş olabilir.
    # Bu tür eksik veriler analizim için işe yaramaz.
    # dropna() fonksiyonu ile bu iki sütundan herhangi biri boş (NaN) olan satırları siliyorum.
    # subset parametresi hangi sütunlara bakılacağını belirtir.
    # inplace=True, değişikliğin doğrudan 'df_temiz' üzerinde yapılmasını sağlar.
    df_temiz.dropna(subset=['Review_Title', 'Review'], inplace=True)
    # Kaç satırın temizlendiğini değil, işlemin yapıldığını bildiriyorum.
    print("- Boş başlık veya boş yorum içeren satırlar temizlendi.")

    # --- Adım 3: Yorum Başlığı ve Metnini Birleştirme ---
    # RAG modelimin her yorum için tek bir metin kaynağına sahip olması daha iyi.
    # Bu yüzden 'Review_Title' ve 'Review' sütunlarını birleştireceğim.
    # apply() metodu, DataFrame'in her satırına ('axis=1') belirlediğim bir işlemi uygular.
    # lambda row: ... ifadesi, her satır ('row') için çalışacak küçük bir fonksiyondur.
    # Bu fonksiyon, başlığı ve yorumu alıp "BASLIK: ... YORUM: ..." formatında birleştirir.
    # Sonucu 'birlesik_yorum' adında yeni bir sütuna yazıyorum.
    df_temiz['birlesik_yorum'] = df_temiz.apply(
        lambda row: f"BASLIK: {row['Review_Title']}\nYORUM: {row['Review']}",
        axis=1
    )
    # İşlemin tamamlandığını bildiriyorum.
    print("- 'Review_Title' ve 'Review' sütunları 'birlesik_yorum' adında tek bir sütunda birleştirildi.")

    # --- Adım 4: Son Sütunları Seçme ---
    # Artık orijinal başlık ve yorum sütunlarına ihtiyacım kalmadı.
    # Sadece 'Airline Name' ve yeni oluşturduğum 'birlesik_yorum' sütunlarını içeren
    # nihai DataFrame'i ('df_son') oluşturuyorum.
    df_son = df_temiz[['Airline Name', 'birlesik_yorum']]
    
    # --- Adım 5: Temiz Veriyi Kaydetme ---
    # Hazırladığım bu temiz ve son veriyi yeni bir CSV dosyasına kaydediyorum.
    # to_csv() fonksiyonu DataFrame'i CSV dosyasına yazar.
    # index=False, pandas'ın otomatik eklediği satır numaralarının dosyaya yazılmasını engeller.
    df_son.to_csv(output_filename, index=False)

    # İşlemin başarıyla tamamlandığını ve sonuç dosyasının adını bildiriyorum.
    print(f"\nİşlem tamamlandı!")
    print(f"'{output_filename}' dosyası başarıyla oluşturuldu.")
    # Oluşturulan dosyada kaç adet yorum olduğunu yazdırıyorum.
    print(f"Toplam {len(df_son)} adet birleştirilmiş ve temizlenmiş yorum mevcut.")
    # Yeni oluşturulan veriden bir önizleme (ilk 5 satır) gösteriyorum.
    print("\nİşte yeni oluşturulan veriden bir örnek:")
    print(df_son.head())

# --- Hata Yakalama Bloğu ---
# Eğer try bloğunda 'FileNotFoundError' (Dosya bulunamadı hatası) oluşursa,
# kullanıcıya dosyayı kontrol etmesi gerektiğini söyleyen bir mesaj yazdırıyorum.
except FileNotFoundError:
    print(f"HATA: '{input_filename}' adında bir dosya bulunamadı.")
    print("Lütfen dosyayı doğru klasöre taşıdığınızdan emin olun.")
# Eğer başka herhangi bir beklenmedik hata oluşursa,
# hatanın ne olduğunu kullanıcıya bildiriyorum.
except Exception as e:
    print(f"Beklenmedik bir hata oluştu: {e}")