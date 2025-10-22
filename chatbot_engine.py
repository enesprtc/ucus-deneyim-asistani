# --- Gerekli Kütüphaneler ---
# pandas: Temizlenmiş CSV verimi okumak ve filtrelemek için. 'pd' kısaltmasıyla kullanacağım.
import pandas as pd
# streamlit: Streamlit Cloud'un Secrets özelliğinden API anahtarımı okumak için. 'st' kısaltmasıyla kullanacağım.
import streamlit as st
# google.generativeai: Google API anahtarını doğrudan yapılandırmak için. 'genai' kısaltmasıyla kullanacağım.
import google.generativeai as genai
# langchain_google_genai: Google'ın Gemini modellerini (Embedding ve Chat) LangChain ile kullanmamı sağlayan kütüphaneler.
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# langchain_community.vectorstores: FAISS vektör veritabanını LangChain ile kullanmamı sağlayan kütüphane.
from langchain_community.vectorstores import FAISS
# langchain.prompts: Dil modeline (LLM) göndereceğim komutları (prompt) yapılandırmak için.
from langchain.prompts import PromptTemplate
# langchain.docstore.document: Metinlerimi ve metadata'larını LangChain'in anlayacağı bir formatta paketlemek için.
from langchain.docstore.document import Document

# --- Genel Ayarlar ve Başlangıç Yüklemeleri ---
# Streamlit Cloud Secrets'tan Google API anahtarını okuyorum.
# Bu, .env dosyası yerine deploy edilen ortamda anahtarı güvenli bir şekilde almamı sağlar.
try:
    GOOGLE_API_KEY = st.secrets["AIzaSyBlmr-uVwxzJXwhQ9Exr04SaI5Jo5LWKY8"]
    # Google'ın kendi kütüphanesini API anahtarıyla yapılandırıyorum.
    # Bu, LangChain'in Google modellerini kullanabilmesi için genellikle gereklidir.
    genai.configure(api_key=GOOGLE_API_KEY)
    print("-> Google API Anahtarı Streamlit Secrets'tan başarıyla yüklendi ve yapılandırıldı.")
except KeyError:
    # Eğer Secrets içinde anahtar bulunamazsa, kullanıcıya hata gösterip duruyorum.
    st.error("Google API Anahtarı (GOOGLE_API_KEY) Streamlit Secrets içinde tanımlanmamış!")
    st.stop() # Uygulamanın çalışmasını durduruyorum.
except Exception as e:
    # Anahtar yapılandırması sırasında başka bir hata olursa onu da gösteriyorum.
    st.error(f"Google API Anahtarı yapılandırılırken bir hata oluştu: {e}")
    st.stop()

# Temizlenmiş veriyi içeren CSV dosyamın adı.
INPUT_FILENAME = "temiz_havayolu_yorumlari.csv"

# --- ADIM 1: Ana Veri Setini Hafızaya Yükleme ---
# Program ilk çalıştığında, tüm temiz yorumları bir kereye mahsus hafızaya (RAM) alıyorum.
print(f"'{INPUT_FILENAME}' okunuyor...")
# Hata kontrolü: Eğer dosya bulunamazsa programı durduruyorum.
try:
    # pandas ile temiz CSV dosyamı okuyup 'df_tum_yorumlar' DataFrame'ine yüklüyorum.
    df_tum_yorumlar = pd.read_csv(INPUT_FILENAME)
    print(f"-> {len(df_tum_yorumlar)} adet yorum başarıyla hafızaya yüklendi.")
except FileNotFoundError:
    # Streamlit arayüzünde hata göstermek için st.error kullanıyorum.
    st.error(f"HATA: '{INPUT_FILENAME}' dosyası bulunamadı. Lütfen dosyanın reponuzda olduğundan emin olun.")
    st.stop()

# --- Embedding Modelini Hazırlama ---
# Metinleri anlamsal parmak izlerine (vektörlere) dönüştürecek olan Google modelini başlatıyorum.
print("Google Embedding Modeli hazırlanıyor...")
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    print("-> Embedding Modeli hazır.")
except Exception as e:
    st.error(f"Embedding modeli başlatılırken hata oluştu: {e}")
    st.stop()


# --- ADIM 2: Ana Chatbot Fonksiyonu ---
# Bu fonksiyon, kullanıcıdan bir soru ve bir havayolu adı alıp, analiz sonucunu döndürecek.
# Streamlit'in @st.cache_data decorator'ünü kullanarak FAISS index oluşturma işlemini hızlandırabiliriz,
# ancak şimdilik basit tutmak için bunu eklemiyorum.
def get_response(soru, havayolu_adi):
    print(f"\n--- Yeni Sorgu ---")
    print(f"Havayolu: '{havayolu_adi}', Soru: '{soru}'")

    # --- Aşama 2.1: Havayoluna Göre Filtreleme ---
    print(f"[Aşama 1] Sadece '{havayolu_adi}' için yorumlar filtreleniyor...")
    df_filtrelenmis = df_tum_yorumlar[df_tum_yorumlar['Airline Name'] == havayolu_adi]

    if df_filtrelenmis.empty:
        return f"'{havayolu_adi}' için sistemde hiç yorum bulunamadı."
    
    print(f"-> {len(df_filtrelenmis)} adet yorum bulundu.")

    # --- Aşama 2.2: Geçici Arama Motorunu (FAISS Index) Oluşturma ---
    print("[Aşama 2] Filtrelenmiş yorumlar için geçici arama motoru oluşturuluyor...")
    documents = [Document(page_content=row['birlesik_yorum'], metadata={'Airline Name': row['Airline Name']}) for index, row in df_filtrelenmis.iterrows()]
    
    try:
        vector_store = FAISS.from_documents(documents, embeddings)
        print("-> Geçici arama motoru hazır.")
    except Exception as e:
        # Hata detayını loglamak (terminalde görmek) ve kullanıcıya genel bir mesaj vermek daha iyi olabilir.
        print(f"FAISS index oluşturma hatası: {e}")
        return "Yorumlar analiz edilirken bir sorun oluştu. Lütfen tekrar deneyin."

    # --- Aşama 2.3: Anlamsal Arama Yapma ---
    print("[Aşama 3] Anlamsal arama yapılıyor...")
    relevant_docs = vector_store.similarity_search(soru, k=5)
    
    if not relevant_docs:
        # Bu durumda bulunan yorumlar içinde soruyla eşleşen bir şey bulunamamıştır.
        return "Bu havayolu ile ilgili belirttiğiniz konuda yorum bulunsa da, sorunuzla doğrudan ilişkili bir detay tespit edilemedi."

    # --- Aşama 2.4: Gemini ile Cevap Üretme ---
    print(f"-> {len(relevant_docs)} adet ilgili yorum bulundu. Gemini ile cevap üretiliyor...")
    
    prompt_template = """
    SENARYO: Sen, yolcu yorumlarını analiz eden bir Uçuş Deneyimi Asistanısın. Görevin, sana sunulan KANITLARI kullanarak, kullanıcının sorduğu SORUYU cevaplamaktır. Cevapların kesinlikle ve sadece sana verilen KANITLARA dayanmalıdır. Cevabını nazik ve anlaşılır bir dille, bir paragraf halinde özetle.

    KANITLAR:
    {context}

    SORU:
    {question}

    CEVAP:
    """
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    # LLM'i burada, fonksiyon içinde tanımlamak yerine en başta tanımlamak daha verimli olabilir,
    # ancak şimdilik burada bırakıyorum. Model adını teyit ettik.
    try:
        llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0.3)
        chain = prompt | llm
        context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
        response = chain.invoke({"context": context, "question": soru})
        return response.content
    except Exception as e:
        # Gemini'den cevap alırken oluşan hataları yakalıyorum.
        print(f"Gemini cevap üretme hatası: {e}")
        # Kullanıcıya daha açıklayıcı bir hata mesajı veriyorum.
        if "API key not valid" in str(e):
             return "Google API anahtarı geçersiz veya yanlış yapılandırılmış. Lütfen Streamlit Secrets ayarlarını kontrol edin."
        elif "quota" in str(e).lower():
             return "Google API kullanım kotası aşıldı. Lütfen bir süre sonra tekrar deneyin."
        else:
             return "Yapay zeka modeliyle iletişim kurulurken bir sorun oluştu."


# --- ADIM 3: Doğrudan Çalıştırma Testi ---
# Bu blok, sadece script'i doğrudan 'python chatbot_engine.py' ile çalıştırdığımızda devreye girer.
# Streamlit uygulamasını çalıştırırken bu kısım çalışmaz, bu yüzden burası test amaçlı kalabilir.
if __name__ == '__main__':
    # Streamlit Secrets burada çalışmayacağı için test bloğu hata verecektir.
    # Lokal test için .env'den okuma yöntemini geçici olarak buraya ekleyebiliriz
    # VEYA bu test bloğunu tamamen kaldırabiliriz, çünkü ana test arayüz üzerinden yapılacak.
    print("\n--- LOKAL TEST BAŞLATILDI (Streamlit olmadan çalıştırıldığında) ---")
    print("UYARI: Bu test, Streamlit Secrets yerine .env dosyasını kullanmayı gerektirebilir.")
    # Lokal test için dotenv'ı burada tekrar yükleyebiliriz:
    from dotenv import load_dotenv
    load_dotenv()
    local_api_key = os.getenv("GOOGLE_API_KEY") # os'u import etmeyi unutma: import os
    if local_api_key:
         genai.configure(api_key=local_api_key)
         print("-> Lokal test için .env'den API anahtarı yüklendi.")
         
         soru1 = "How was the food and the seats?"
         havayolu1 = "Turkish Airlines"
         cevap1 = get_response(soru1, havayolu1)
         print("\n--- CHATBOT CEVABI 1 ---\n", cevap1)
    else:
         print("-> Lokal test için .env dosyasında GOOGLE_API_KEY bulunamadı. Test atlanıyor.")