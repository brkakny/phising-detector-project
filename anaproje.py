import pandas as pd
import re
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

print("Veri seti yukleniyor...")
df = pd.read_csv("phishing_email.csv") # csv dosyasını içeri alıyoruz buradan

# veri oranını %70'e çıkardım ki model daha çok mail görüp iyice akıllansın
df = df.sample(frac=0.7, random_state=42) 

def temizle(metin):
    if pd.isna(metin): return "" # boş satır gelirse hata vermesin diye
    metin = metin.lower() # her şeyi küçük harf yapıyoruz karışıklık olmasın
    metin = re.sub(r'<.*?>', '', metin) # html etiketlerini falan temizledim burada
    metin = re.sub(r'[^a-z\s]', '', metin) # sadece harfler kalsın istedim, en temiz sonuç böyle çıkıyor
    return metin.strip() # sağdaki soldaki boşlukları siliyoruz son olarak

print("Metinler temizleniyor...")
df['temiz_metin'] = df['text_combined'].apply(temizle) # temizlik fonksiyonunu tüm sütuna uyguladık

print("TF-IDF donusumu yapiliyor...")
# kelimeleri sayılara döküyoruz model anlasın diye, 5000 kelime sınırı koydum boyut artmasın
vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
X = vectorizer.fit_transform(df['temiz_metin'])
y = df['label'] # hedef etiketimiz burada

# verinin %20'sini test için ayırdık ki model ne kadar öğrenmiş görelim
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Model egitiliyor (Guclendirilmis Mod)...")
# ağaç sayısını 100 yaptık ve derinlik sınırını kaldırdık ki model her detayı öğrensin
model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=None, 
    class_weight='balanced', 
    random_state=42,
    n_jobs=-1 # bilgisayarın tüm gücünü kullansın hızlı bitsin
)
model.fit(X_train, y_train) # eğitimi başlatıyoruz

print("\n--- MODEL PERFORMANS RAPORU ---")
y_pred = model.predict(X_test) # test verisiyle tahmin yapıyoruz
print(classification_report(y_test, y_pred, target_names=['Guvenli', 'Phishing']))

print("Hata matrisi olusturuluyor...")
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Guvenli', 'Phishing'], 
            yticklabels=['Guvenli', 'Phishing'])
plt.xlabel('Tahmin Edilen')
plt.ylabel('Gercek Deger')
plt.title('Phishing Tespit Sistemi Hata Matrisi')
plt.show()

print("SHAP analizi calistiriliyor...")
# modelin neden böyle karar verdiğini anlamak için shap kullanıyoruz
X_test_small = X_test[:10].toarray() # sadece 10 tanesine baksak yeter uzun sürmesin
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test_small, check_additivity=False)

vals = shap_values[1] if isinstance(shap_values, list) else shap_values

# shap grafiğini çizdiriyoruz, en etkili 15 kelimeyi görelim dedik
shap.summary_plot(vals, X_test_small, 
                  feature_names=vectorizer.get_feature_names_out(), 
                  plot_type="bar", 
                  max_display=15,
                  show=False) 

plt.title("Yapay Zeka Karar Analizi: En Etkili 15 Kelime (SHAP)", fontsize=14, pad=20)
plt.xlabel("Ortalama Etki Gücü (SHAP Değeri)", fontsize=10)
plt.gcf().set_size_inches(10, 6) # boyutu biraz büyüttük net olsun
plt.tight_layout()

plt.savefig('kesin_sonuc_shap.png', bbox_inches='tight') # resmi kaydediyoruz jüriye göstermek için
print("Grafik 'kesin_sonuc_shap.png' adıyla kaydedildi.")
plt.show()

# eğitilen modeli ve kelime vektörlerini kaydediyoruz ki app.py içinde kullanabilelim
joblib.dump(model, 'phishing_model.pkl', compress=3) # sıkıştırdık boyut küçük kalsın
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
print("Guclendirilmis model dosyaları kaydedildi!")