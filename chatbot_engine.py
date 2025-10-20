# --- Gerekli Kütüphaneler ---
# pandas: Temizlenmiş CSV verimi okumak ve filtrelemek için. 'pd' kısaltmasıyla kullanacağım.
import pandas as pd
# dotenv: .env dosyasındaki gizli API anahtarımı güvenli bir şekilde yüklemek için.
from dotenv import load_dotenv
# langchain_google_genai: Google'ın Gemini modellerini (Embedding ve Chat) LangChain ile kullanmamı sağlayan kütüphaneler.
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
# langchain_community.vectorstores: FAISS vektör veritabanını LangChain ile kullanmamı sağlayan kütüphane.
from langchain_community.vectorstores import FAISS
# langchain.prompts: Dil modeline (LLM) göndereceğim komutları (prompt) yapılandırmak için.
from langchain.prompts import PromptTemplate
# langchain.docstore.document: Metinlerimi ve metadata'larını LangChain'in anlayacağı bir formatta paketlemek için.
from langchain.docstore.document import Document

# --- Genel Ayarlar ve Başlangıç Yüklemeleri ---
# .env dosyasındaki değişkenleri (özellikle GOOGLE_API_KEY) ortam değişkeni olarak yüklüyorum.
load_dotenv()
# Temizlenmiş veriyi içeren CSV dosyamın adı.
INPUT_FILENAME = "temiz_havayolu_yorumlari.csv"

# --- ADIM 1: Ana Veri Setini Hafızaya Yükleme ---
# Program ilk çalıştığında, tüm temiz yorumları bir kereye mahsus hafızaya (RAM) alıyorum.
# Bu, her soru geldiğinde dosyayı tekrar tekrar okumaktan çok daha hızlıdır.
print(f"'{INPUT_FILENAME}' okunuyor...")
# Hata kontrolü: Eğer dosya bulunamazsa programı durduruyorum.
try:
    # pandas ile temiz CSV dosyamı okuyup 'df_tum_yorumlar' DataFrame'ine yüklüyorum.
    df_tum_yorumlar = pd.read_csv(INPUT_FILENAME)
    # Kaç yorum yüklendiğini kullanıcıya bildiriyorum.
    print(f"-> {len(df_tum_yorumlar)} adet yorum başarıyla hafızaya yüklendi.")
except FileNotFoundError:
    print(f"!!! HATA: '{INPUT_FILENAME}' dosyası bulunamadı. Lütfen 'veri_hazirla.py' script'ini çalıştırdığınızdan emin olun.")
    # Dosya yoksa programın devam etmesinin anlamı yok, çıkıyorum.
    exit()

# --- Embedding Modelini Hazırlama ---
# Metinleri anlamsal parmak izlerine (vektörlere) dönüştürecek olan Google modelini başlatıyorum.
# Bu modeli hem geçici veritabanı oluştururken hem de arama yaparken kullanacağım için en başta hazırlıyorum.
print("Google Embedding Modeli hazırlanıyor...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
print("-> Embedding Modeli hazır.")

# --- ADIM 2: Ana Chatbot Fonksiyonu ---
# Bu fonksiyon, kullanıcıdan bir soru ve bir havayolu adı alıp, analiz sonucunu döndürecek.
def get_response(soru, havayolu_adi):
    # Kullanıcıya hangi havayolu ve soru için işlem yapıldığını bildiriyorum.
    print(f"\n--- Yeni Sorgu ---")
    print(f"Havayolu: '{havayolu_adi}', Soru: '{soru}'")

    # --- Aşama 2.1: Havayoluna Göre Filtreleme ---
    # İlk iş olarak, hafızadaki tüm yorumlar ('df_tum_yorumlar') içinden sadece
    # kullanıcının seçtiği havayoluna ('havayolu_adi') ait olanları filtreliyorum.
    print(f"[Aşama 1] Sadece '{havayolu_adi}' için yorumlar filtreleniyor...")
    # pandas DataFrame filtreleme: 'Airline Name' sütunu 'havayolu_adi' ile eşleşen satırları seçiyorum.
    df_filtrelenmis = df_tum_yorumlar[df_tum_yorumlar['Airline Name'] == havayolu_adi]

    # Eğer filtreleme sonucunda hiç yorum bulunamazsa, kullanıcıya bilgi verip fonksiyondan çıkıyorum.
    if df_filtrelenmis.empty:
        return f"'{havayolu_adi}' için sistemde hiç yorum bulunamadı."
    
    # Kaç adet yorum bulunduğunu bildiriyorum.
    print(f"-> {len(df_filtrelenmis)} adet yorum bulundu.")

    # --- Aşama 2.2: Geçici Arama Motorunu (FAISS Index) Oluşturma ---
    # Sadece filtrelenmiş bu yorumları kullanarak, o anlık, küçük bir vektör veritabanı oluşturacağım.
    print("[Aşama 2] Filtrelenmiş yorumlar için geçici arama motoru oluşturuluyor...")
    # LangChain'in Document formatına dönüştürmek için boş bir liste başlatıyorum.
    documents = []
    # Filtrelenmiş DataFrame'deki her bir satır için döngü başlatıyorum.
    for index, row in df_filtrelenmis.iterrows():
        # Her yorumu, içeriği ('birlesik_yorum') ve metadata'sı ('Airline Name') ile
        # bir Document nesnesi olarak paketliyorum.
        doc = Document(page_content=row['birlesik_yorum'], metadata={'Airline Name': row['Airline Name']})
        # Oluşturduğum Document nesnesini listeye ekliyorum.
        documents.append(doc)
    
    # FAISS index'ini oluştururken hata oluşma ihtimaline karşı try-except kullanıyorum.
    try:
        # FAISS.from_documents() metodu, verdiğim doküman listesini ve embedding modelini kullanarak
        # hafızada (RAM'de) hızlı bir vektör veritabanı oluşturur.
        vector_store = FAISS.from_documents(documents, embeddings)
        print("-> Geçici arama motoru hazır.")
    # Eğer embedding sırasında (örn. kota aşımı) bir hata olursa, kullanıcıya bilgi verip çıkıyorum.
    except Exception as e:
        return f"Arama motoru oluşturulurken bir hata oluştu: {e}"

    # --- Aşama 2.3: Anlamsal Arama Yapma ---
    # Artık elimde sadece ilgili havayolunun yorumlarını içeren küçük ve hızlı bir arama motoru var.
    print("[Aşama 3] Anlamsal arama yapılıyor...")
    # vector_store.similarity_search() metodu, kullanıcının sorusuna ('soru') anlamsal olarak
    # en çok benzeyen ilk 'k' adet dokümanı bulur. k=5 olarak ayarladım.
    # Artık burada filtre kullanmama gerek yok, çünkü veritabanı zaten filtrelenmişti.
    relevant_docs = vector_store.similarity_search(soru, k=5)
    
    # Eğer arama sonucunda hiç alakalı doküman bulunamazsa, kullanıcıya bilgi verip çıkıyorum.
    if not relevant_docs:
        return "Bu havayolu ile ilgili belirttiğiniz konuda yeterli yorum bulunamadı."

    # --- Aşama 2.4: Gemini ile Cevap Üretme ---
    # Arama sonucu bulunan doküman sayısını kullanıcıya bildiriyorum.
    print(f"-> {len(relevant_docs)} adet ilgili yorum bulundu. Gemini ile cevap üretiliyor...")
    
    # Gemini'ye göndereceğim komutun (prompt) şablonunu hazırlıyorum.
    # Bu şablon, Gemini'ye rolünü, görevini ve kullanması gereken kanıtları (context) anlatıyor.
    prompt_template = """
    SENARYO: Sen, yolcu yorumlarını analiz eden bir Uçuş Deneyimi Asistanısın. Görevin, sana sunulan KANITLARI kullanarak, kullanıcının sorduğu SORUYU cevaplamaktır. Cevapların kesinlikle ve sadece sana verilen KANITLARA dayanmalıdır. Cevabını nazik ve anlaşılır bir dille, bir paragraf halinde özetle.

    KANITLAR:
    {context}

    SORU:
    {question}

    CEVAP:
    """
    
    # LangChain'in PromptTemplate'ini kullanarak şablonu bir nesneye dönüştürüyorum.
    # input_variables, şablondaki {context} ve {question} alanlarını belirtir.
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    # Cevap üretecek olan Gemini modelini (LLM - Large Language Model) başlatıyorum.
    # temperature=0.3, cevapların daha tutarlı ve daha az rastgele olmasını sağlar.
    llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0.3) # Model adını teyit ettik.
    # LangChain "zincirini" (chain) oluşturuyorum. '|' operatörü, prompt'un çıktısını LLM'in girdisi yapar.
    chain = prompt | llm
    # Arama sonucu bulduğum dokümanların ('relevant_docs') sadece metin içeriklerini ('page_content')
    # alıp, aralarına ayraç koyarak tek bir metin bloğu ('context') haline getiriyorum.
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
    # Zinciri çalıştırıyorum! invoke() metodu, şablondaki yer tutucuları (context ve question)
    # doldurur, prompt'u oluşturur, LLM'e gönderir ve cevabı alır.
    response = chain.invoke({"context": context, "question": soru})
    
    # LLM'den gelen cevabın sadece metin içeriğini ('content') fonksiyondan döndürüyorum.
    return response.content

# --- ADIM 3: Doğrudan Çalıştırma Testi ---
# Eğer bu script dosyası doğrudan çalıştırılırsa (başka bir dosya tarafından import edilmezse),
# aşağıdaki kod bloğu çalışır. Bu, motorumu hızlıca test etmek için kullanışlıdır.
if __name__ == '__main__':
    # Test 1: Turkish Airlines için bir soru soruyorum.
    soru1 = "How was the food and the seats?"
    havayolu1 = "Turkish Airlines"
    # get_response fonksiyonumu çağırıp cevabı alıyorum.
    cevap1 = get_response(soru1, havayolu1)
    # Aldığım cevabı ekrana yazdırıyorum.
    print("\n--- CHATBOT CEVABI 1 ---\n", cevap1)

    # Test 2: Pegasus Airlines için başka bir soru soruyorum.
    soru2 = "What are the common complaints about the staff?"
    havayolu2 = "Pegasus Airlines"
    # get_response fonksiyonumu tekrar çağırıp cevabı alıyorum.
    cevap2 = get_response(soru2, havayolu2)
    # Aldığım ikinci cevabı da ekrana yazdırıyorum.
    print("\n--- CHATBOT CEVABI 2 ---\n", cevap2)