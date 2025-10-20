# --- Gerekli Kütüphaneler ---
# Streamlit kütüphanesini 'st' kısaltmasıyla içeri aktarıyorum.
# Bu kütüphane, Python ile interaktif web uygulamaları oluşturmamı sağlıyor.
import streamlit as st
# time kütüphanesini, cevabı ekrana yazarken küçük bir gecikme efekti vermek için kullanacağım.
import time

# --- Chatbot Motorunu İçeri Aktarma ---
# Kendi yazdığım 'chatbot_engine.py' dosyasından ana fonksiyonumu ('get_response')
# ve tüm yorumları içeren DataFrame'i ('df_tum_yorumlar') içeri aktarıyorum.
try:
    from chatbot_engine import get_response, df_tum_yorumlar
# Eğer 'chatbot_engine.py' bulunamazsa veya içindeki gerekli öğeler eksikse,
# kullanıcıya bir hata mesajı gösterip uygulamayı durduruyorum. Bu önemli bir güvenlik önlemi.
except (ModuleNotFoundError, ImportError):
    st.error("Kritik Hata: 'chatbot_engine.py' dosyası bulunamadı veya gerekli fonksiyonlar içe aktarılamadı.")
    st.stop()

# --- Sayfa Genel Ayarları ---
# Web sayfamın tarayıcı sekmesindeki başlığını, sayfa düzenini (geniş ekran)
# ve sekme ikonunu (emoji) ayarlıyorum.
st.set_page_config(page_title="Uçuş Deneyim Asistanı", layout="wide", page_icon="✈️")

# --- ARKA PLAN VE GÖRSEL STİL AYARLARI (CSS) ---
# Uygulamanın genel görünümünü CSS (Cascading Style Sheets) kullanarak özelleştiriyorum.
# CSS kodunu bir Python string'i içine yazıyorum.
page_bg_img = """
<style>
/* Streamlit uygulamasının ana kapsayıcısını hedefliyorum (.stApp) */
.stApp {
    /* Arka plan resmi ayarlıyorum. Resmin üzerine yarı saydam siyah bir filtre ekliyorum (okunabilirlik için). */
    background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url("https://images.pexels.com/photos/96622/pexels-photo-96622.jpeg");
    /* Resmin tüm ekranı kaplamasını sağlıyorum. */
    background-size: cover;
    /* Resmin ortalanmasını sağlıyorum. */
    background-position: center center;
    /* Resmin tekrarlanmasını engelliyorum. */
    background-repeat: no-repeat;
    /* Sayfa kaydırılsa bile arka planın sabit kalmasını sağlıyorum. */
    background-attachment: fixed;
}

/* Uygulama içindeki tüm ana metinlerin (başlıklar, paragraflar, etiketler) rengini beyaz yapıyorum. */
.stApp, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
.stSelectbox label, .stTextArea label, [data-testid="stCaptionContainer"] {
    color: white !important; /* '!important' diğer stilleri ezmesini sağlar. */
}

/* Alt başlığın (h3) yazı boyutunu biraz küçültüyorum. */
h3 { font-size: 1.25em !important; }

/* Açılır kapanır kutuların (Expander) görünümünü ayarlıyorum. */
[data-testid="stExpander"] {
    background-color: rgba(255, 255, 255, 0.1); /* Hafif beyaz, saydam arka plan */
    border-radius: 10px; /* Köşeleri yuvarlatıyorum. */
}

/* Seçim kutusu (Selectbox) ve metin alanı (TextArea) etiketlerinin rengini beyaz yapıyorum. */
.stSelectbox label, .stTextArea label {
    color: white !important;
}

/* Sayfa altındaki küçük notun (Caption) rengini ayarlıyorum. */
[data-testid="stCaptionContainer"] {
    color: rgba(255, 255, 255, 0.7) !important; /* Biraz daha soluk beyaz */
}

/* Chatbot cevabını göstereceğim özel kutunun stilini tanımlıyorum. */
.response-box {
    background-color: rgba(0, 100, 200, 0.1); /* Yarı saydam mavi arka plan */
    color: white; /* Yazı rengi beyaz */
    padding: 15px; /* İç boşluk */
    border-radius: 10px; /* Köşeleri yuvarlatıyorum. */
    font-size: 1em; /* Yazı boyutu */
    line-height: 1.6; /* Satır aralığı */
}

</style>
"""
# Hazırladığım bu CSS kodunu st.markdown() ve unsafe_allow_html=True ile sayfaya ekliyorum.
st.markdown(page_bg_img, unsafe_allow_html=True)
# ----------------------------------------------------

# --- Sağ Üst Köşe Dekoratif Uçak (YORUM SATIRI) ---
# Buraya daha önce bir uçak resmi eklemiştim ama şimdilik kaldırdım.
# İstersem bu yorum satırlarını kaldırıp tekrar ekleyebilirim.
# top_col1, top_col2 = st.columns([4, 1])
# with top_col2:
#     st.image("https://www.pngall.com/wp-content/uploads/12/Airplane-PNG-Images.png", width=150)

# --- Ana Başlık ve Alt Başlık ---
# Sayfanın ana başlığını emoji ile birlikte ayarlıyorum.
st.title("✈️ Uçuş Deneyim Asistanı")
# Ana başlığın altına, daha küçük puntoyla bir alt başlık ekliyorum.
st.markdown("### Yapay zeka ile on binlerce yolcu yorumunu analiz eden Uçuş Deneyim Asistanı ile havayolları hakkında merak ettiğiniz her şeyi öğrenin!")
# Kullanılan verinin tarih aralığı hakkında küçük bir bilgilendirme notu ekliyorum.
st.caption("Not: Analiz edilen yolcu yorumları 2023 yılına kadar olan verileri kapsamaktadır.")

# --- Arayüzü Ana Sütunlara Ayırma ---
# Sayfayı iki ana sütuna ayırıyorum. Sol sütun (col1) daha geniş (2 birim),
# sağ sütun (col2) daha dar (1 birim) olacak. 'gap="large"' sütunlar arasına boşluk bırakır.
col1, col2 = st.columns([2, 1], gap="large")

# --- SOL SÜTUN: Kullanıcı Etkileşim Alanı ---
# 'with col1:' bloğu içindeki her şey sol sütunda görünecek.
with col1:
    # Kullanıcının havayolu seçmesini sağlayacak bir açılır liste (Selectbox) oluşturuyorum.
    # Önce tüm benzersiz havayolu isimlerini 'df_tum_yorumlar' DataFrame'inden alıp sıralıyorum.
    # Listenin başına boş bir seçenek ("") ekliyorum ki başlangıçta bir şey seçili olmasın.
    airline_list = [""] + sorted(df_tum_yorumlar['Airline Name'].unique())
    # st.selectbox() fonksiyonu ile açılır listeyi oluşturuyorum.
    # İlk parametre etiketi, 'options' liste seçeneklerini, 'help' ise üzerine gelince çıkacak ipucunu belirtir.
    selected_airline = st.selectbox(
        "1. Havayolunu Seçin:",
        options=airline_list,
        help="Hakkında bilgi almak istediğiniz havayolunu bu listeden seçin."
    )

    # Kullanıcının sorusunu yazacağı çok satırlı bir metin alanı (TextArea) oluşturuyorum.
    user_question = st.text_area(
        "2. Sorunuzu Yazın:",
        height=150, # Metin kutusunun yüksekliği
        placeholder="Örnek: Koltuk konforu ve diz mesafesi nasıldı?", # Kutunun içinde görünecek örnek metin
        help="Sorunuzu Türkçe veya İngilizce olarak sorabilirsiniz." # Yardım metni
    )

    # "Yorumları Analiz Et" butonunu oluşturuyorum.
    # 'type="primary"' butonu daha belirgin yapar. 'use_container_width=True' butonun sütuna yayılmasını sağlar.
    if st.button("Yorumları Analiz Et 🚀", type="primary", use_container_width=True):
        # Butona tıklandığında çalışacak kod bloğu:
        # Önce hem havayolunun seçildiğini hem de sorunun yazıldığını kontrol ediyorum.
        if selected_airline and user_question:
            # Cevap üretilirken kullanıcıya bir bekleme animasyonu ('spinner') gösteriyorum.
            with st.spinner(f"Lütfen bekleyin... '{selected_airline}' için yorumlar analiz ediliyor..."):
                # İşte motorumu çağırdığım yer! 'chatbot_engine.py'deki fonksiyonumu
                # seçilen havayolu ve soru ile çağırıyorum.
                response = get_response(user_question, selected_airline)
                
                # Cevap geldikten sonra, görsel bir ayırıcı çizgi ekliyorum.
                st.divider()
                # Cevap başlığını ekliyorum.
                st.subheader("🤖 Asistanın Analiz Sonucu:", anchor=False)

                # --- Cevabı özel stil ile gösteriyorum ---
                # st.info() yerine, yukarıda CSS ile tanımladığım 'response-box' stilini kullanarak
                # cevabı daha şık bir kutu içinde gösteriyorum. f-string ve HTML kullandığım için
                # unsafe_allow_html=True parametresini ekliyorum.
                st.markdown(f'<div class="response-box">{response}</div>', unsafe_allow_html=True)
        # Eğer havayolu seçilmemişse veya soru yazılmamışsa, kullanıcıyı uyarıyorum.
        else:
            st.warning("Lütfen hem bir havayolu seçin hem de sorunuzu yazın.")

# --- SAĞ SÜTUN: Bilgilendirme Alanı ---
# 'with col2:' bloğu içindeki her şey sağ sütunda görünecek.
with col2:
    # Sağ sütundaki kutuların soldakilerle daha iyi hizalanması için küçük bir boşluk ekliyorum.
    st.markdown("<br>", unsafe_allow_html=True) # Hafifçe aşağı kaydırmak için

    # Açılır kapanır bir kutu (Expander) oluşturuyorum. Başlangıçta kapalı olacak.
    with st.expander("❓ Bu Uygulama Ne İşe Yarar?"):
        # Kutunun içine açıklama metnini yazıyorum.
        st.write(
            """
            Uçuş Deneyimi Asistanına hoş geldiniz! Bu RAG (Retrieval-Augmented Generation) tabanlı yapay zeka asistanı,
            on binlerce doğrulanmış yolcu yorumunu sizin için analiz eder.

            Soldaki listeden hakkında bilgi almak istediğiniz havayolunu seçin ve koltuk konforu,
            yemek servisi, personel tutumu veya uçak içi eğlence gibi konularda merak ettiğiniz soruları sorun.
            Asistan, ilgili yorumları bulup sizin için özetleyecektir.
            """
        )

    # İkinci bir açılır kapanır kutu oluşturuyorum.
    with st.expander("💡 Örnek Sorular"):
        # İçine örnek soruları yazıyorum.
        st.write(
            """
            - Yemek servisindeki genel şikayetler nelerdir?
            - Uçak içi eğlence sistemi nasıl?
            - Kabin ekibinin profesyonelliği ve tutumu hakkında bilgi ver.
            """
        )

# --- SAYFANIN EN ALTI: Footer ---
# İçerik alanından ayırmak için bir çizgi ekliyorum.
st.markdown("---")
# Footer (sayfa alt bilgisi) için CSS stilini tanımlıyorum.
footer_css = """
<style>
.footer {
    position: fixed; /* Sayfa kaysa bile altta sabit kalmasını sağlar. */
    left: 0;
    bottom: 0;
    width: 100%; /* Tüm sayfa genişliğini kaplar. */
    background-color: rgba(0, 0, 0, 0.5); /* Yarı saydam siyah arka plan */
    color: rgba(255, 255, 255, 0.7); /* Hafif soluk beyaz yazı rengi */
    text-align: center; /* Metni ortalar. */
    padding: 10px; /* İç boşluk */
    font-size: 0.9em; /* Biraz daha küçük yazı boyutu */
}
</style>

<div class="footer">
    Geliştiren: Enes Pırtıcı | Akbank Generative AI Bootcamp Projesi
</div>
"""
# Hazırladığım CSS ve HTML'i sayfaya ekliyorum.
st.markdown(footer_css, unsafe_allow_html=True)