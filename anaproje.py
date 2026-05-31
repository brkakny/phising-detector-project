import pandas as pd
import re
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import shap
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.tree import DecisionTreeClassifier

print("Veri seti yukleniyor ve isleniyor...")
df = pd.read_csv("combined_dataset.csv")
# Verideki gereksiz yerleri ayıklıyoruz, aaron gibi isimler kafamızı karıştırmasın
df = df[~df['text'].str.contains('aaron', case=False, na=False)]
df = df[~df['text'].str.contains(' aa ', case=False, na=False)]
df = df.sample(frac=1.0, random_state=42) 

def temizle(metin):
    """Metin verisini NLP modellerine hazirlamak icin temizleme fonksiyonu."""
    if pd.isna(metin): return ""
    metin = metin.lower()
    metin = re.sub(r'<.*?>', '', metin) # HTML etiketlerini ayikla
    metin = re.sub(r'[^a-zçğıöşü\s]', '', metin) # Sadece harflere odaklan
    return metin.strip()

print("Metin temizleme islemleri yurutuluyor...")
df['temiz_metin'] = df['text'].apply(temizle)

# NLP öncesi belirli kelimeleri eliyoruz
turkce_stop_words = ["bir", "ve", "bu", "ise", "veya", "için", "olan", "çok", "daha", "de", "da"]
print("TF-IDF veri donusumu yapiliyor...")

# min_df=5 ile kelime havuzunu daraltıp daha rafine bir model hedefliyoruz
vectorizer = TfidfVectorizer(
    max_features=5000, 
    ngram_range=(1,2),
    stop_words=turkce_stop_words + ['english'],
    min_df=5
)

X = vectorizer.fit_transform(df['temiz_metin'])
y = df['label']

# Veriyi %80 eğitim, %20 test olarak bölüyoruz
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

modeller = {
    "Random Forest": RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1),
    "Logistic Regression": LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42),
    "Naive Bayes": MultinomialNB(),
    "Decision Tree": DecisionTreeClassifier(class_weight='balanced', random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(n_estimators=100, random_state=42)
}

en_iyi_skor = 0
en_iyi_model_adi = ""
en_iyi_model_nesnesi = None

print("\n--- Model Performans Karsilastirmalari ---")
for ad, model in modeller.items():
    model.fit(X_train, y_train)
    skor = model.score(X_test, y_test)
    print(f"{ad} dogruluk orani: %{skor*100:.2f}")
    
    if skor > en_iyi_skor:
        en_iyi_skor = skor
        en_iyi_model_adi = ad
        en_iyi_model_nesnesi = model

print(f"\nSecilen optimize algoritma: {en_iyi_model_adi}")

# Model performansinin hata matrisi ile gorsellestirilmesi
y_pred = en_iyi_model_nesnesi.predict(X_test)
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=['Guvenli', 'Phishing'], yticklabels=['Guvenli', 'Phishing'])
plt.title(f'Hata Matrisi - {en_iyi_model_adi}')
plt.show()

# Modelin karar mekanizmasini aciklayan SHAP analizi
#shap analizi geliştirilecek tam istenen isterlerimiz elde edilemiyor
print("SHAP analizi calistiriliyor...")
X_test_small = X_test[:10].toarray()

if en_iyi_model_adi in ["Random Forest", "Decision Tree", "Gradient Boosting"]:
    explainer = shap.TreeExplainer(en_iyi_model_nesnesi)
    shap_values = explainer.shap_values(X_test_small, check_additivity=False)
    vals = shap_values[1] if isinstance(shap_values, list) else shap_values
else:
    explainer = shap.Explainer(en_iyi_model_nesnesi, X_train[:100].toarray())
    shap_values = explainer(X_test_small)
    vals = shap_values.values

shap.summary_plot(vals, X_test_small, 
                  feature_names=vectorizer.get_feature_names_out(), 
                  plot_type="bar", max_display=10, show=False) 

plt.title(f"AI Karar Analizi: En Etkili 10 Kelime ({en_iyi_model_adi})")
plt.savefig('kesin_sonuc_shap.png', bbox_inches='tight')
plt.show()

# Optimize edilen modelin deployment icin kaydedilmesi
joblib.dump(en_iyi_model_nesnesi, 'phishing_model.pkl', compress=3)
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')
print("Model ve vektörize nesneleri başarıyla kaydedildi.")