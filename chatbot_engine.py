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

# --- Genel Ayarlar ve Başlangıç Yüklemeleri ---

# --- API Anahtarını Yükleme (Hem Lokal hem Cloud için GÜNCELLENDİ) ---
GOOGLE_API_KEY = None # Başlangıçta anahtar yok.

# Önce Streamlit Secrets'ı deniyoruz (Cloud ortamı için).
# Secrets'a erişirken herhangi bir hata olursa (KeyError veya dosya bulunamadı hatası),
# except bloğuna geçeceğiz.
try:
    print("-> Streamlit Secrets deneniyor...")
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    print("-> Google API Anahtarı Streamlit Secrets'tan yüklendi.")
# Eğer Secrets'ta anahtar yoksa VEYA Secrets dosyası bulunamadıysa (lokaldeysek), .env dosyasını deniyoruz.
except Exception as e: # KeyError yerine daha genel Exception yakalıyoruz.
    print(f"-> Streamlit Secrets kullanılamadı ({type(e).__name__}), .env dosyası deneniyor...")
    load_dotenv() # .env dosyasını yükle
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        print("-> Google API Anahtarı .env dosyasından yüklendi.")
    else:
        # Ne Secrets'ta ne de .env'de anahtar yoksa hata verip duruyoruz.
        st.error("Google API Anahtarı (GOOGLE_API_KEY) ne Streamlit Secrets'ta ne de .env dosyasında bulunamadı!")
        st.stop()

# --- Google API'ını Yapılandırma ---
# Anahtarı bulduktan sonra Google servisini yapılandırıyoruz.
if GOOGLE_API_KEY:
    try:
         genai.configure(api_key=GOOGLE_API_KEY)
         print("-> Google API Anahtarı başarıyla yapılandırıldı.")
    except Exception as e:
         st.error(f"Google API Anahtarı yapılandırılırken hata: {e}")
         st.stop()
else:
     # Bu satıra normalde ulaşmamalıyız ama güvenlik için ekleyelim.
     st.error("API Anahtarı yüklenemediği için Google API yapılandırılamadı.")
     st.stop()
# -----------------------------------------------------------------

INPUT_FILENAME = "temiz_havayolu_yorumlari.csv"

# --- ADIM 1: Ana Veri Setini Hafızaya Yükleme ---
# @st.cache_data decorator'ünü ekleyerek bu pahalı işlemi önbelleğe alıyoruz.
# Bu, uygulamanın her etkileşimde CSV'yi tekrar okumasını engeller ve hızı artırır.
@st.cache_data
def load_data(filename):
    print(f"'{filename}' okunuyor (Önbelleğe alınıyor)...")
    try:
        df = pd.read_csv(filename)
        print(f"-> {len(df)} adet yorum başarıyla hafızaya yüklendi.")
        return df
    except FileNotFoundError:
        st.error(f"HATA: '{filename}' dosyası bulunamadı. Lütfen dosyanın reponuzda olduğundan emin olun.")
        st.stop() # Hata durumunda uygulamayı durdur

# Veriyi yükleme fonksiyonunu çağırıyoruz.
df_tum_yorumlar = load_data(INPUT_FILENAME)


# --- Embedding Modelini Hazırlama ---
# @st.cache_resource decorator'ü ile bu modeli de önbelleğe alıyoruz.
# Modelin her seferinde yeniden başlatılmasını engeller.
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

# Embedding modelini yükleme fonksiyonunu çağırıyoruz.
embeddings = load_embeddings_model()


# --- ADIM 2: Ana Chatbot Fonksiyonu ---
# Bu fonksiyon artık önbelleğe alınmış veriyi ve modeli kullanacak.
def get_response(soru, havayolu_adi):
    print(f"\n--- Yeni Sorgu ---")
    print(f"Havayolu: '{havayolu_adi}', Soru: '{soru}'")

    print(f"[Aşama 1] Sadece '{havayolu_adi}' için yorumlar filtreleniyor...")
    df_filtrelenmis = df_tum_yorumlar[df_tum_yorumlar['Airline Name'] == havayolu_adi]

    if df_filtrelenmis.empty:
        return f"'{havayolu_adi}' için sistemde hiç yorum bulunamadı."
    
    print(f"-> {len(df_filtrelenmis)} adet yorum bulundu.")

    print("[Aşama 2] Filtrelenmiş yorumlar için geçici arama motoru oluşturuluyor...")
    documents = [Document(page_content=row['birlesik_yorum'], metadata={'Airline Name': row['Airline Name']}) for index, row in df_filtrelenmis.iterrows()]
    
    try:
        # Embedding modeli artık dışarıdan hazır geliyor.
        vector_store = FAISS.from_documents(documents, embeddings)
        print("-> Geçici arama motoru hazır.")
    except Exception as e:
        print(f"FAISS index oluşturma hatası: {e}")
        return "Yorumlar analiz edilirken bir sorun oluştu. Lütfen tekrar deneyin."

    print("[Aşama 3] Anlamsal arama yapılıyor...")
    relevant_docs = vector_store.similarity_search(soru, k=5)
    
    if not relevant_docs:
        return "Bu havayolu ile ilgili belirttiğiniz konuda yorum bulunsa da, sorunuzla doğrudan ilişkili bir detay tespit edilemedi."

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
    try:
        # LLM'i burada tanımlıyoruz. Bunu da önbelleğe alabiliriz ama şimdilik basit tutalım.
        llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0.3)
        chain = prompt | llm
        context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
        response = chain.invoke({"context": context, "question": soru})
        return response.content
    except Exception as e:
        print(f"Gemini cevap üretme hatası: {e}")
        if "API key not valid" in str(e):
             return "Google API anahtarı geçersiz veya yanlış yapılandırılmış. Lütfen Streamlit Secrets veya .env dosyasını kontrol edin."
        elif "quota" in str(e).lower():
             return "Google API kullanım kotası aşıldı. Lütfen bir süre sonra tekrar deneyin."
        else:
             return "Yapay zeka modeliyle iletişim kurulurken bir sorun oluştu."


# --- ADIM 3: Doğrudan Çalıştırma Testi ---
# Bu blok lokal test için hala geçerli, çünkü anahtar yükleme mekanizması artık lokalde .env'i buluyor.
if __name__ == '__main__':
    print("\n--- LOKAL TEST BAŞLATILDI (Streamlit olmadan çalıştırıldığında) ---")
    if GOOGLE_API_KEY:
         soru1 = "How was the food and the seats?"
         havayolu1 = "Turkish Airlines"
         cevap1 = get_response(soru1, havayolu1)
         print("\n--- CHATBOT CEVABI 1 ---\n", cevap1)
    else:
         print("-> Lokal test için API anahtarı bulunamadı. Test atlanıyor.")