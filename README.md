# ✈️ Uçuş Deneyimi Asistanı

Akbank GenAI Bootcamp kapsamında geliştirilen RAG tabanlı bir chatbot projesidir.

## Projenin Amacı
Bu projenin amacı, on binlerce doğrulanmış yolcu yorumunu kullanarak, belirli bir havayolu hakkında sorulan sorulara (koltuk konforu, yemek servisi, personel tutumu vb.) yapay zeka destekli özet cevaplar üretmektir. Kullanıcılar, merak ettikleri havayolunu seçip sorularını sorarak, o havayolu hakkındaki genel eğilimleri ve yolcu deneyimlerini hızlıca öğrenebilirler.

## Veri Seti Hakkında Bilgi
Projede, Kaggle platformunda bulunan "[Airline Reviews](https://www.kaggle.com/datasets/juhibhojani/airline-reviews)" veri seti kullanılmıştır. Bu veri seti, farklı havayolları için yapılmış binlerce yolcu yorumunu içermektedir. Veri hazırlama aşamasında (`veri_hazirla.py`):
* Sadece `Airline Name`, `Review_Title` ve `Review` sütunları alınmıştır.
* Boş yorumlar temizlenmiştir.
* `Review_Title` ve `Review` sütunları tek bir metin alanında birleştirilerek analiz için hazır hale getirilmiştir (`temiz_havayolu_yorumlari.csv`).
* *Not: Analiz edilen yorumlar 2023 yılına kadar olan verileri kapsamaktadır.*

## Kullanılan Yöntemler (Çözüm Mimarisi)
Bu proje, RAG (Retrieval-Augmented Generation) mimarisi üzerine kurulmuştur. Kullanılan temel teknolojiler şunlardır:
* **Web Arayüzü:** Streamlit
* **Veri İşleme:** Pandas
* **Dil Modeli (LLM):** Google Gemini API (örn: `gemini-flash-latest`)
* **Embedding Modeli:** Google (`models/embedding-001`)
* **Vektör Veritabanı:** FAISS (Facebook AI Similarity Search)
* **Orkestrasyon:** LangChain

**Çalışma Prensibi:**
1.  Kullanıcı arayüzden bir havayolu seçer ve sorusunu sorar.
2.  Sistem, `pandas` kullanarak hafızadaki tüm yorumlardan sadece seçilen havayoluna ait olanları filtreler.
3.  Sadece bu filtrelenmiş yorumlar kullanılarak, Google Embedding modeli ile vektörlere dönüştürülür ve **o anlık, geçici bir FAISS veritabanı** hafızada oluşturulur.
4.  Kullanıcının sorusu da vektöre çevrilir ve bu geçici FAISS veritabanında anlamsal olarak en benzer yorumlar (`similarity_search`) bulunur.
5.  Bulunan en alakalı yorumlar (kanıtlar) ve kullanıcının orijinal sorusu, önceden tanımlanmış bir prompt şablonu kullanılarak Google Gemini modeline gönderilir.
6.  Gemini, bu kanıtlara dayanarak soruyu özetleyen bir cevap üretir ve arayüzde gösterilir.

## Elde Edilen Sonuçlar
Geliştirilen asistan, seçilen havayolu özelinde sorulan sorulara, ilgili yolcu yorumlarından derlenmiş özet cevaplar üretebilmektedir. Örneğin:
* _(Buraya birkaç başarılı soru-cevap örneği ekran görüntüsü veya metin olarak eklenebilir)_

## Çalışma Kılavuzu
Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyebilirsiniz:
1.  **Repository'yi Klonlayın:**
    ```bash
    git clone [https://github.com/KULLANICI_ADIN/REPO_ADIN.git](https://github.com/KULLANICI_ADIN/REPO_ADIN.git)
    cd REPO_ADIN
    ```
2.  **Sanal Ortam Oluşturun ve Aktive Edin:**
    ```bash
    python -m venv venv
    # Windows için:
    venv\Scripts\activate
    # Mac/Linux için:
    source venv/bin/activate
    ```
3.  **Gerekli Kütüphaneleri Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **API Anahtarını Ayarlayın:** Proje ana dizininde `.env` adında bir dosya oluşturun ve içine kendi Google API anahtarınızı aşağıdaki formatta ekleyin:
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```
5.  **Uygulamayı Başlatın:**
    ```bash
    streamlit run app.py
    ```
6.  Açılan web tarayıcı sekmesinde uygulamayı kullanmaya başlayın.

## Product Kılavuzu (Web Arayüzü Kullanımı)
Uygulamayı kullanmak oldukça basittir:
1.  **Havayolunu Seçin:** Sol paneldeki "1. Havayolunu Seçin:" başlıklı açılır menüden hakkında bilgi almak istediğiniz havayolunu seçin.
2.  **Sorunuzu Yazın:** "2. Sorunuzu Yazın:" başlıklı metin alanına merak ettiğiniz soruyu Türkçe veya İngilizce olarak yazın. (Örn: "Koltuklar rahat mıydı?", "How was the food service?")
3.  **Analiz Edin:** "Yorumları Analiz Et 🚀" butonuna tıklayın.
4.  **Sonucu Görüntüleyin:** Kısa bir analiz süresinin ardından, asistanın bulduğu yorumlara dayanarak ürettiği özet cevap sol panelin altında görünecektir.
* _(Buraya arayüzün ekran görüntüleri eklenebilir)_

## Web Linki
Uygulamanın canlı demosuna aşağıdaki linkten erişebilirsiniz:
**(Buraya Streamlit Cloud'a deploy ettikten sonra alacağın link gelecek)**
