# --- Gerekli Kütüphaneler ---
import pandas as pd
import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
# Dil tespiti için ekledim (basit bir yöntem)
from langdetect import detect, LangDetectException 

# --- Genel Ayarlar ve Başlangıç Yüklemeleri ---

# --- API Anahtarını Yükleme (Hem Lokal hem Cloud için) ---
GOOGLE_API_KEY = None 
try:
    print("-> Streamlit Secrets deneniyor...")
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    print("-> Google API Anahtarı Streamlit Secrets'tan yüklendi.")
except Exception as e: 
    print(f"-> Streamlit Secrets kullanılamadı ({type(e).__name__}), .env dosyası deneniyor...")
    load_dotenv() 
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        print("-> Google API Anahtarı .env dosyasından yüklendi.")
    else:
        st.error("Google API Anahtarı (GOOGLE_API_KEY) ne Streamlit Secrets'ta ne de .env dosyasında bulunamadı!")
        st.stop()

# --- Google API'ını Yapılandırma ---
if GOOGLE_API_KEY:
    try:
         genai.configure(api_key=GOOGLE_API_KEY)
         print("-> Google API Anahtarı başarıyla yapılandırıldı.")
    except Exception as e:
         st.error(f"Google API Anahtarı yapılandırılırken hata: {e}")
         st.stop()
else:
     st.error("API Anahtarı yüklenemediği için Google API yapılandırılamadı.")
     st.stop()

INPUT_FILENAME = "temiz_havayolu_yorumlari.csv"

# --- ADIM 1: Ana Veri Setini Hafızaya Yükleme ---
@st.cache_data
def load_data(filename):
    print(f"'{filename}' okunuyor (Önbelleğe alınıyor)...")
    try:
        df = pd.read_csv(filename)
        print(f"-> {len(df)} adet yorum başarıyla hafızaya yüklendi.")
        return df
    except FileNotFoundError:
        st.error(f"HATA: '{filename}' dosyası bulunamadı. Lütfen dosyanın reponuzda olduğundan emin olun.")
        st.stop() 

df_tum_yorumlar = load_data(INPUT_FILENAME)

# --- Embedding Modelini Hazırlama ---
@st.cache_resource
def load_embeddings_model():
    print("Google Embedding Modeli hazırlanıyor (Önbelleğe alınıyor)...")
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        print("-> Embedding Modeli hazır.")
        return embeddings_model
    except Exception as e:
        st.error(f"Embedding modeli başlatılırken hata oluştu: {e}")
        st.stop()

embeddings = load_embeddings_model()

# --- Dil Tespiti ve Çeviri İçin LLM ---
# Cevap üretimi ve potansiyel çeviri/dil tespiti için LLM'i burada tanımlıyoruz.
# @st.cache_resource # Bunu da önbelleğe alabiliriz.
def load_llm():
    print("Ana Dil Modeli (LLM) hazırlanıyor...")
    try:
        # Model adını teyit ettiğimiz en stabil ve çalışan modelle güncelleyelim.
        llm_model = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0.3) 
        print("-> LLM hazır.")
        return llm_model
    except Exception as e:
         st.error(f"Ana Dil Modeli başlatılırken hata oluştu: {e}")
         st.stop()

llm = load_llm() # LLM'i en başta bir kere yüklüyoruz.

# --- ADIM 2: Ana Chatbot Fonksiyonu ---
def get_response(soru, havayolu_adi):
    print(f"\n--- Yeni Sorgu ---")
    print(f"Havayolu: '{havayolu_adi}', Orjinal Soru: '{soru}'")

    # --- YENİ ADIM: DİL TESPİTİ ---
    try:
        orjinal_dil = detect(soru) # 'tr' veya 'en' gibi bir dil kodu döner.
        print(f"-> Tespit edilen soru dili: {orjinal_dil}")
    except LangDetectException:
        print("-> Soru dili tespit edilemedi, İngilizce varsayılıyor.")
        orjinal_dil = "en" # Tespit edilemezse İngilizce kabul edelim.
    except Exception as e:
        print(f"-> Dil tespiti sırasında hata: {e}. İngilizce varsayılıyor.")
        orjinal_dil = "en"


    # --- YENİ ADIM: KOŞULLU ÇEVİRİ ---
    if orjinal_dil == "tr":
        print("[Aşama 1a] Soru İngilizce'ye çevriliyor...")
        try:
            translation_prompt = f"Translate the following Turkish text to English, keeping the meaning and keywords intact: '{soru}'"
            arama_sorusu = llm.invoke(translation_prompt).content
            print(f"-> Çevrilen Soru (Arama için): '{arama_sorusu}'")
        except Exception as e:
            print(f"-> Çeviri hatası: {e}. Orijinal soru ile devam edilecek.")
            arama_sorusu = soru # Çeviri başarısız olursa orijinal soruyla dene
    else:
        # Soru zaten İngilizce ise veya dil tespit edilemediyse, doğrudan kullanıyoruz.
        arama_sorusu = soru
        print("[Aşama 1a] Soru zaten İngilizce, çeviriye gerek yok.")
    # ------------------------------------

    print(f"[Aşama 1b] Sadece '{havayolu_adi}' için yorumlar filtreleniyor...")
    df_filtrelenmis = df_tum_yorumlar[df_tum_yorumlar['Airline Name'] == havayolu_adi]

    if df_filtrelenmis.empty:
        return f"'{havayolu_adi}' için sistemde hiç yorum bulunamadı."
    
    print(f"-> {len(df_filtrelenmis)} adet yorum bulundu.")

    print("[Aşama 2] Filtrelenmiş yorumlar için geçici arama motoru oluşturuluyor...")
    documents = [Document(page_content=row['birlesik_yorum'], metadata={'Airline Name': row['Airline Name']}) for index, row in df_filtrelenmis.iterrows()]
    
    try:
        vector_store = FAISS.from_documents(documents, embeddings)
        print("-> Geçici arama motoru hazır.")
    except Exception as e:
        print(f"FAISS index oluşturma hatası: {e}")
        return "Yorumlar analiz edilirken bir sorun oluştu. Lütfen tekrar deneyin."

    print("[Aşama 3] Anlamsal arama (İngilizce soru ile) yapılıyor...")
    # Aramayı HER ZAMAN İngilizce soruyla yapıyoruz.
    relevant_docs = vector_store.similarity_search(arama_sorusu, k=5) 
    
    if not relevant_docs:
        # Orijinal dilde cevap veriyoruz.
        if orjinal_dil == "tr":
            return "Bu havayolu ile ilgili belirttiğiniz konuda yorum bulunsa da, sorunuzla doğrudan ilişkili bir detay tespit edilemedi."
        else:
            return "Although reviews were found for this airline, no specific details related to your query could be identified."

    print(f"-> {len(relevant_docs)} adet ilgili yorum bulundu. Gemini ile cevap üretiliyor...")
    
    # --- YENİ ADIM: DİNAMİK CEVAP DİLİ ---
    # Cevabın hangi dilde olması gerektiğini belirliyoruz.
    cevap_dili = "Turkish" if orjinal_dil == "tr" else "English"
    
    # Prompt şablonunu cevap dilini içerecek şekilde güncelliyoruz.
    prompt_template = f"""
    SENARYO: Sen, İngilizce yolcu yorumlarını analiz eden bir Uçuş Deneyimi Asistanısın.
    Görevin, sana sunulan İngilizce KANITLARI kullanarak, kullanıcının sorduğu SORUYU {cevap_dili} dilinde cevaplamaktır.
    Cevapların kesinlikle ve sadece sana verilen KANITLARA dayanmalıdır.
    Cevabını nazik, anlaşılır ve akıcı bir şekilde, bir paragraf halinde {cevap_dili} olarak özetle.

    İngilizce KANITLAR:
    {{context}}

    Kullanıcının Orijinal SORUSU:
    {{question}}

    {cevap_dili} CEVAP:
    """
    # ------------------------------------
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    try:
        # LLM zaten en başta yüklenmişti.
        chain = prompt | llm 
        context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
        # Zinciri çalıştırırken orijinal soruyu ('soru') kullanıyoruz.
        response = chain.invoke({"context": context, "question": soru}) 
        return response.content
    except Exception as e:
        print(f"Gemini cevap üretme hatası: {e}")
        # Hata mesajını da orijinal dilde vermek daha iyi olabilir.
        error_message_tr = "Yapay zeka modeliyle iletişim kurulurken bir sorun oluştu."
        error_message_en = "An issue occurred while communicating with the AI model."
        if "API key not valid" in str(e):
             error_message_tr = "Google API anahtarı geçersiz veya yanlış yapılandırılmış."
             error_message_en = "Google API key is invalid or misconfigured."
        elif "quota" in str(e).lower():
             error_message_tr = "Google API kullanım kotası aşıldı. Lütfen bir süre sonra tekrar deneyin."
             error_message_en = "Google API usage quota exceeded. Please try again later."

        return error_message_tr if orjinal_dil == "tr" else error_message_en


# --- ADIM 3: Doğrudan Çalıştırma Testi ---
if __name__ == '__main__':
    print("\n--- LOKAL TEST BAŞLATILDI ---")
    if GOOGLE_API_KEY:
         # Test 1: Türkçe Soru
         soru1_tr = "Yemekler ve koltuklar nasıldı?"
         havayolu1 = "Turkish Airlines"
         cevap1 = get_response(soru1_tr, havayolu1)
         print("\n--- CHATBOT CEVABI 1 (TÜRKÇE SORU) ---\n", cevap1)

         # Test 2: İngilizce Soru
         soru2_en = "What are the common complaints about the staff?"
         havayolu2 = "Pegasus Airlines"
         cevap2 = get_response(soru2_en, havayolu2)
         print("\n--- CHATBOT CEVABI 2 (İNGİLİZCE SORU) ---\n", cevap2)
    else:
         print("-> Lokal test için API anahtarı bulunamadı. Test atlanıyor.")