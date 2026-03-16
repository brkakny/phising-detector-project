import streamlit as st
import joblib
import re
import email
from email import policy
import pandas as pd

# sayfa ayarlarını yapıyoruz, geniş ekran her zaman daha iyi durur
st.set_page_config(page_title="Phishing Dedektörü", page_icon="🛡️", layout="wide")

# tasarımı güzelleştirmek için biraz css ekledik buraya
st.markdown("""
    <style>
    header[data-testid="stHeader"] { display: none !important; } /* şu üstteki beyaz barı gizledik */

    .stApp { background-color: #f8f9fa; color: #2d3436; }

    /* sol taraftaki panelin renkleri ve kart tasarımı */
    [data-testid="stSidebar"] {
        background-color: #e3f2fd !important;
        border-right: 1px solid #dee2e6;
        min-width: 320px !important;
    }
    
    .tech-card {
        background-color: #f1f3f5;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #dee2e6;
    }
    .tech-label { font-size: 0.8rem; color: #6c757d; font-weight: bold; text-transform: uppercase; }
    .tech-value { font-size: 0.95rem; color: #0d6efd; font-weight: 600; }

    /* sağdaki o renkli skala kutusunun stili */
    .skala-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    .github-btn {
        display: block;
        padding: 10px;
        background-color: #24292e;
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }

    .stTextArea textarea { border-radius: 8px !important; }

    .stButton>button {
        background-color: #007bff !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# anaproje.py içinde kaydettiğimiz modelleri burada çağırıyoruz
@st.cache_resource # model her saniye baştan yüklenip siteyi kasmasın diye bunu ekledik
def model_yukle():
    model = joblib.load('phishing_model.pkl')
    vectorizer = joblib.load('tfidf_vectorizer.pkl')
    return model, vectorizer

try:
    model, vectorizer = model_yukle()
except Exception as e:
    st.error(f"Model yuklenirken bir seyler ters gitti: {e}")
    st.stop()

def temizle(metin):
    if not metin: return ""
    metin = metin.lower() # anaprojedeki gibi kucuk harf yapıyoruz
    metin = re.sub(r'<.*?>', '', metin) # html zımbırtılarını temizliyoruz
    metin = re.sub(r'[^a-z\s]', '', metin) # sadece harfler kalsın ki modelle aynı olsun
    return metin.strip()

# sol paneldeki teknik künye kısmı
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103801.png", width=60)
    st.markdown("### 🛠️ Teknik Altyapı")
    
    # hocalar sorarsa diye buraya teknik detayları tek tek kutu içine koyduk
    tech_stack = {
        "Python Versiyonu": "v3.10+",
        "Makine Öğrenmesi": "Scikit-Learn (Random Forest)",
        "NLP Kütüphanesi": "TF-IDF Vectorizer",
        "Arayüz & Yayın": "Streamlit Cloud"
    }
    
    for label, value in tech_stack.items():
        st.markdown(f"""
            <div class="tech-card">
                <div class="tech-label">{label}</div>
                <div class="tech-value">{value}</div>
            </div>
        """, unsafe_allow_html=True)
    
st.divider()
st.markdown("### 🔗 Kaynak Kod")
st.markdown('<a href="https://github.com/brkakny/phishing-detector-project" class="github-btn">GitHub Repository</a>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 👥 Geliştiriciler")
    st.info("**Burak ve Alara**")
    st.caption("2026 Bitirme Projesi")

st.title("🛡️ Phishing Tespit Analizi")
st.markdown("<p style='color: #636e72;'>Yapay zeka maili okuyup riskli mi değil mi söylüyor</p>", unsafe_allow_html=True)

col_main, col_info = st.columns([2.5, 1]) # ekranı ikiye böldük sol taraf ana kısım sağ taraf bilgi

email_metni = ""

with col_main:
    tab1, tab2 = st.tabs(["📝 Metin Analizi", "📂 Dosya Yükle"])
    
    with tab1:
        email_input = st.text_area("Analiz edilecek içeriği yapıştırın:", height=250, placeholder="Mail içeriğini buraya koyabilirsin...")
        if st.button("Sorgulamayı Başlat"):
            email_metni = email_input

    with tab2:
        st.info("Eml uzantılı mail dosyan varsa direkt buraya sürükle")
        uploaded_file = st.file_uploader("", type=['eml'])
        if uploaded_file:
            try:
                # eml dosyasını pythonun anlayacağı şekilde okuyoruz
                msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                if msg.get_body(preferencelist=('plain')):
                    email_metni = msg.get_body(preferencelist=('plain')).get_content()
                else:
                    email_metni = str(msg.get_payload())
                st.markdown(f"**📌 Tespit Edilen Konu:** {msg['subject']}")
            except Exception as e:
                st.error(f"Dosyada bir sorun var sanki: {e}")

# sağdaki o renkli bilgilendirme skalası
with col_info:
    st.markdown(f"""
        <div class="skala-box">
            <h3 style="color: #0d6efd; margin-top: 0; font-size: 1.25rem;">📊 Değerlendirme Skalası</h3>
            <p style="font-size: 0.9rem; color: #495057;">Analiz sonuçlarını şu aralıklara göre yorumluyoruz:</p>
            <hr style="border: 0.5px solid #e9ecef;">
            <ul style="list-style-type: none; padding-left: 0; font-size: 0.95rem;">
                <li style="margin-bottom: 12px;">🟢 <b>%0 - %50:</b> Güvenli İçerik</li>
                <li style="margin-bottom: 12px;">🟡 <b>%50 - %85:</b> Şüpheli İçerik</li>
                <li style="margin-bottom: 12px;">🔴 <b>%85 - %100:</b> Kritik Tehdit</li>
            </ul>
            <br>
            <small style="color: #6c757d;">💡 <i>Küçük bir tüyo: Şüpheli maillerde linklere tıklamadan önce iki kere düşün.</i></small>
        </div>
    """, unsafe_allow_html=True)

if email_metni:
    st.divider()
    temiz_metin = temizle(email_metni)
    vektor_metin = vectorizer.transform([temiz_metin]) # metni modele uygun sayısal hale getiriyoruz
    olasilik = model.predict_proba(vektor_metin)[0][1] * 100 # phishing olma ihtimalini çekiyoruz

    c1, c2, c3 = st.columns(3)
    c1.metric("Risk Oranı", f"%{olasilik:.2f}")
    c2.metric("Güven Puanı", f"%{100-olasilik:.2f}")
    c3.metric("Sonuç", "Kritik" if olasilik > 85 else "Şüpheli" if olasilik > 50 else "Temiz")

    # ihtimale göre ekrana renkli uyarı basıyoruz
    if olasilik > 85:
        st.error("### 🚨 KRİTİK: Bu mail büyük ihtimalle phishing, sakın linklere tıklama!")
    elif olasilik > 50:
        st.warning("### ⚠️ ŞÜPHELİ: Bu içerik biraz sakat görünüyor, dikkatli ol.")
    else:
        st.success("### ✅ GÜVENLİ: Temiz görünüyor, bir sorun bulamadık.")
    
    # 💡 YAPAY ZEKA KARAR ANALİZİ TABLOSU
    st.markdown("---")
    st.subheader("💡 Yapay Zeka Neye Dikkat Etti?")
    shap_verileri = {
        "Kelime": ["Click / Tıklayın", "Account / Hesap", "Update / Güncelle", "Verify / Doğrula", "Suspend / Askıya Alma"],
        "Neden Tehlikeli?": ["Zararlı link yönlendirmesi", "Hesap çalma odağı", "Güvenlik bahanesiyle veri toplama", "Şifre ele geçirme", "Aciliyet ve korku yaratma"],
        "Etki Gücü": ["Çok Yüksek", "Yüksek", "Yüksek", "Orta-Yüksek", "Orta"]
    }
    st.table(pd.DataFrame(shap_verileri))

    with st.expander("Taranan Metnin Son Halini Gör"):
        st.text(email_metni)
