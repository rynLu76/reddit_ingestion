import spacy
import string
from textblob import TextBlob
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from heapq import nlargest
from spacy import displacy
import sklearn
# from spacy import Tokenizer
from spacy.lang.en import English
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import LancasterStemmer, WordNetLemmatizer
import sentence_transformers
import bertopic
from sentence_transformers import SentenceTransformer
# import umap
# from umap import UMAP
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer
from nltk.stem.snowball import SnowballStemmer
from nltk.stem import WordNetLemmatizer
import re
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, \
    ElementClickInterceptedException, NoSuchWindowException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from praw.exceptions import InvalidURL
import time


def pre_processing(text):
    if text == "":
        return text
    else:
        text = re.sub(r"(?:\@|http?\://|https?\://|www)\S+", " ", text)
        text = re.sub(r"won\'t", "will not", text)  # fix contractions
        text = re.sub(r"can\'t", "can not", text)
        text = re.sub(r"n\'t", " not", text)
        text = re.sub(r"\'re", " are", text)
        text = re.sub(r"\'s", " is", text)
        text = re.sub(r"\'d", " would", text)
        text = re.sub(r"\'ll", " will", text)
        text = re.sub(r"\'t", " not", text)
        text = re.sub(r"\'ve", " have", text)
        text = re.sub(r"\'m", " am", text)
        text = re.sub(r"[^a-zA-z]", " ", text)
        text = re.sub("(^|\W)\d+($|\W)", " ", text)
        text = re.sub('\W+', ' ', text)
        text = re.sub(r"\s+", " ", text)
        text = text.lower()
        text = text.strip()
        # text = "".join([i for i in str(text) if i not in string.punctuation])

    return text


def remove_punctuations(text):
    if text == "":
        punctuationfree = ""
    else:
        punctuationfree="".join([i for i in str(text) if i not in string.punctuation])
    return punctuationfree


# def tokenize_text(text):
#     if text == "":
#         result = [text]
#     else:
#         nlp = English()
#         tokenizer = Tokenizer(nlp.vocab)
#         words = tokenizer(text)
#         result = list(words)
#     return result


def remove_stopwords(text):
    nlp = English()
    tokenizer = nlp.tokenizer
    stop_words = set(stopwords.words("english"))
    if text == "":
        result = [text]
    else:
        text = pre_processing(text)
        text_tokens = tokenizer(text)
        result = [i.text for i in text_tokens if not i.text in stop_words]
    return " ".join(result)


def get_polarity(text):
    return round(TextBlob(text).sentiment.polarity, 2)


def get_subjectivity(text):
    return round(TextBlob(text).sentiment.subjectivity, 2)


def get_sentiment(score):
    if score < 0:
        if score < -0.5:
            return "Very Negative"
        else:
            return "Negative"
        return -1
    elif score == 0:
        return "Neutral"
    else:
        if score > 0.5:
            return "Very Postitive"
        else:
            return "Positive"


def neg_get_entities(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append(ent)

    return entities


def neg_get_labels(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    labels = []
    for ent in doc.ents:
        labels.append(ent.label_)

    return labels


def ngram_frequency(n, text):
    if len(text.split(" ")) >= 3:
        word_vectorizer = CountVectorizer(ngram_range=(n, n), analyzer='word', stop_words=None)
        sparse_matrix = word_vectorizer.fit_transform([text])
        frequencies = sum(sparse_matrix).toarray()[0]
        review_review_unigram = pd.DataFrame(frequencies, index=word_vectorizer.get_feature_names_out(),
                                             columns=['frequency']).sort_values(by=['frequency'], ascending=False)
        result = review_review_unigram[:5].index.values.tolist()
    else:
        result = text
    return result


def filtering_weighing_summarizing(text):
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    text = re.sub(r"(?:\@|http?\://|https?\://|www)\S+", " ", text)
    text = re.sub(r"\\n", " ", text)

    if len(list(doc.sents)) >= 2:
        keyword = []
        stopwords = list(STOP_WORDS)
        pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
        for token in doc:
            if token.text in stopwords or token.text in punctuation:
                continue
            if token.pos_ in pos_tag:
                keyword.append(token.text)

        freq_words = Counter(keyword)
        max_freq = Counter(keyword).most_common(1)[0][1]

        for word in freq_words.keys():
            freq_words[word] = freq_words[word] / max_freq

        sent_strength = {}

        for sent in doc.sents:
            for word in sent:
                if word.text in freq_words.keys():
                    if sent in sent_strength.keys():
                        sent_strength[sent] += freq_words[word.text]
                    else:
                        sent_strength[sent] = freq_words[word.text]

        summ_sentences = nlargest(1, sent_strength, key=sent_strength.get)

        final_sentences = [s.text for s in summ_sentences]

        result = ' '.join(final_sentences)

    else:
        result = text

    return result


def top_nelements(df_ngram, n):
    mapp = {}
    for idx, row in df_ngram.items():
        for word in row:
            if word in mapp:
                mapp[word] += 1
            else:
                mapp[word] = 1

    dict = {k: v for k, v in sorted(mapp.items(), key=lambda item: item[1], reverse=True)}

    df_unigram = pd.DataFrame([dict]).T
    df_unigram = df_unigram.rename(columns={0:'count'})
    return df_unigram.head(n)


def read_csv_to_dataframe(path):
    df = pd.read_csv(path)
    return df


def select_columns_to_analysis(df, **kwargs):
    df = df[[col for col in kwargs.values()]]
    return df
