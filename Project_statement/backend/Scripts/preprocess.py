import re
import nltk
import pandas as pd
from nltk.corpus import stopwords

# Download once
try:
    STOP_WORDS = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    STOP_WORDS = set(stopwords.words("english"))

FINANCE_NOISE = {
    "rs", "inr", "upi", "txn", "tx", "imps", "neft",
    "ref", "bank", "payment", "order"
}

def clean_text(text: str) -> str:
    """Cleans a single transaction description string"""
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r"[/_-]", " ", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)

    words = text.split()
    cleaned = [
        w for w in words
        if w not in STOP_WORDS
        and w not in FINANCE_NOISE
        and len(w) > 2
    ]

    return " ".join(cleaned)

def clean_dataframe(df, text_column):
    """Cleans a dataframe column and returns cleaned df"""
    df = df.copy()
    df["clean_description"] = df[text_column].apply(clean_text)
    df = df[df["clean_description"] != ""]
    return df