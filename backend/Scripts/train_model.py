import pandas as pd
import joblib
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report

# 1. SETUP PATHS
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "Raw.csv"
MODEL_OUTPUT = BASE_DIR / "Scripts" / "model.pkl"
VECTORIZER_OUTPUT = BASE_DIR / "Scripts" / "vectorizer.pkl"

# Add parent to sys.path so we can import preprocess
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
from Scripts.preprocess import clean_text

def train():
    if not DATA_PATH.exists():
        print(f"❌ Error: {DATA_PATH} not found. Please create the training CSV.")
        return

    # 2. LOAD & CLEAN DATA
    df = pd.read_csv(DATA_PATH)
    print(f"📊 Loaded {len(df)} transactions for training.")
    
    # Handle NaN in Category
    df = df.dropna(subset=['Category'])  # Drop rows with NaN in Category
    print(f"📊 After dropping NaN: {len(df)} transactions.")
    
    df['Description'] = df['Description'].fillna('').astype(str).apply(clean_text)
    
    # Remove empty descriptions after cleaning
    df = df[df['Description'] != ""]

    # 3. VECTORIZE
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    X = vectorizer.fit_transform(df['Description'])
    y = df['Category']

    # 4. TRAIN/TEST SPLIT
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 5. TRAIN MODEL
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    
    # Cross-validation check
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"📈 Cross-Validation Accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f})")
    
    model.fit(X_train, y_train)

    # 6. EVALUATE
    y_pred = model.predict(X_test)
    print(f"✅ Hold-out Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print("\n📝 Classification Report:")
    print(classification_report(y_test, y_pred))

    # 7. SAVE TO 'ml/' FOLDER
    joblib.dump(model, MODEL_OUTPUT)
    joblib.dump(vectorizer, VECTORIZER_OUTPUT)
    print(f"💾 Model saved to: {MODEL_OUTPUT}")
    print(f"💾 Vectorizer saved to: {VECTORIZER_OUTPUT}")

if __name__ == "__main__":
    train()