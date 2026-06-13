import pandas as pd
import joblib
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# 1. SETUP PATHS
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "training_data.csv"
MODEL_OUTPUT = BASE_DIR / "Scripts" / "model.pkl"

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
    df = df.dropna(subset=['Category'])
    print(f"📊 After dropping NaN: {len(df)} transactions.")
    
    df['Description'] = df['Description'].fillna('').astype(str).apply(clean_text)
    df = df[df['Description'] != ""]

    # 3. FEATURE ENGINEERING (Text + Numeric Amount)
    X = df[['Description', 'Amount']]  # DataFrame with both columns
    y = df['Category']

    # ColumnTransformer for combined features
    preprocessor = ColumnTransformer(
        transformers=[
            ('text', TfidfVectorizer(ngram_range=(1,3), max_features=4000), 'Description'),  # Updated to (1,3) for better context
            ('num', StandardScaler(), ['Amount'])
        ]
    )

    # 4. TRAIN/TEST SPLIT
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 5. OPTIMIZED MODEL (Faster & Better)
    base_rf = RandomForestClassifier(
        n_estimators=50,      # Faster than 100
        max_depth=20,         # Prevents overfitting
        class_weight='balanced',
        n_jobs=-1             # Parallel processing
    )
    model = CalibratedClassifierCV(base_rf, method='sigmoid', cv=3)  # Faster calibration

    # Pipeline
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])
    pipeline.fit(X_train, y_train)

    # Cross-validation
    cv_scores = cross_val_score(pipeline, X, y, cv=3)
    print(f"📈 Cross-Validation Accuracy: {cv_scores.mean():.2f} (+/- {cv_scores.std() * 2:.2f})")

    # Evaluate
    y_pred = pipeline.predict(X_test)
    print(f"✅ Hold-out Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print("\n📝 Classification Report:")
    print(classification_report(y_test, y_pred))

    # Save Pipeline (includes preprocessor)
    joblib.dump(pipeline, MODEL_OUTPUT)
    print(f"💾 Model saved to: {MODEL_OUTPUT}")

if __name__ == "__main__":
    train()