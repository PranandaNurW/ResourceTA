import pandas as pd
from bertopic import BERTopic

import string
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

try:
    stopwords.words('english')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

CSV_FILE = "/home/ubuntu/tor-scraper/tor-scrape.csv"
BERT_MODEL = "/home/ubuntu/medint-app/teddit_model"

def preprocess_data():
    try:
        df = pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        print("CSV file not found")

    preprocessed_data = []
    for i, row in df.iterrows():
        text = row['title']
        text = text.lower()
        text_p = "".join([char for char in text if char not in string.punctuation])

        words = word_tokenize(text_p)
        words = [word for word in words if word.isalpha()]

        stop_words = stopwords.words('english')
        filtered_words = [word for word in words if word not in stop_words]

        lemmatizer = WordNetLemmatizer()
        stemmed = [lemmatizer.lemmatize(word) for word in filtered_words]
        preprocessed_data.append(stemmed)
    return preprocessed_data

def train_data():
    pre_data = preprocess_data()
    data = [" ".join(words) for words in pre_data]

    params = {
        "embedding_model": "all-MiniLM-L6-v2",
        "nr_topics": 10,
        "min_topic_size": 10,
        "verbose": True,
    }

    topic_model = BERTopic(**params)
    topics, probs = topic_model.fit_transform(data)
    print(topic_model.get_topic_info())
    topic_model.save(BERT_MODEL)

def get_trend_data():
    try:
        df = pd.read_csv(CSV_FILE, index_col=False)
    except FileNotFoundError:
        print("CSV file not found")

    model = BERTopic.load(BERT_MODEL)
    topics = model.get_topic_info().iloc[1:]
    related_news_list = []
    for topic in topics.Name:
        list_topic = topic.split("_")[1:]
        list_topic2 = topic.split("_")[1:3]
        q_topic = "|".join(list_topic2)
        related_news = {
            "related_article": df[df.title.str.contains(q_topic, na=False)].values[:1].tolist(),
            "topic": list_topic,
        }
        related_news_list.append(related_news)
    return related_news_list

if __name__ == "__main__":
    train_data()