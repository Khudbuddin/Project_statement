import re
import pandas as pd

# Lazy import to avoid initial load issues
STOP_WORDS = None

def _get_stop_words():
    global STOP_WORDS
    if STOP_WORDS is None:
        try:
            import nltk
            from nltk.corpus import stopwords
            try:
                STOP_WORDS = set(stopwords.words("english"))
            except LookupError:
                nltk.download("stopwords")
                STOP_WORDS = set(stopwords.words("english"))
        except ImportError:
            # Fallback if nltk not available
            STOP_WORDS = set(["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"])
    return STOP_WORDS

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
    stop_words = _get_stop_words()
    cleaned = [
        w for w in words
        if w not in stop_words
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