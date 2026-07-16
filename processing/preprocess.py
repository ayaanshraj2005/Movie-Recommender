import string
import pickle
import pandas as pd
import ast
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Object for porterStemmer
ps = PorterStemmer()
# Check and download nltk stopwords automatically if missing
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
import streamlit as st

@st.cache_resource
def load_pickle(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

@st.cache_resource
def load_dataframe_from_pickle(file_path):
    with open(file_path, 'rb') as f:
        dict_data = pickle.load(f)
    df = pd.DataFrame.from_dict(dict_data)
    df.reset_index(drop=True, inplace=True)
    return df



def get_genres(obj):
    lista = ast.literal_eval(obj)
    l1 = []
    for i in lista:
        l1.append(i['name'])
    return l1


def get_cast(obj):
    a = ast.literal_eval(obj)
    l_ = []
    len_ = len(a)
    for i in range(0, 10):
        if i < len_:
            l_.append(a[i]['name'])
    return l_


def get_crew(obj):
    l1 = []
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            l1.append(i['name'])
            break
    return l1


def read_csv_to_df():
    #  Reading both the csv files
    credit_ = pd.read_csv(r'Files/tmdb_5000_credits.csv')
    movies = pd.read_csv(r'Files/tmdb_5000_movies.csv')

    # Merging the dataframes by unique ID to prevent cross-product duplicate row issues
    credit_clean = credit_.drop(columns=['title'])
    movies = movies.merge(credit_clean, left_on='id', right_on='movie_id')

    movies2 = movies
    movies2.drop(['homepage', 'tagline'], axis=1, inplace=True)
    movies2 = movies2[['movie_id', 'title', 'budget', 'overview', 'popularity', 'release_date', 'revenue', 'runtime',
                       'spoken_languages', 'status', 'vote_average', 'vote_count']]

    #  Extracting important and relevant features
    movies = movies[
        ['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'production_companies', 'release_date']]
    movies.dropna(inplace=True)

    # df[df['column_name'] == some_condition]['target_column'] = new_value
    # df.loc[df['column_name'] == some_condition, 'target_column'] = new_value

    #  Applying functions to convert from list to only items.
    movies['genres'] = movies['genres'].apply(get_genres)
    movies['keywords'] = movies['keywords'].apply(get_genres)
    movies['top_cast'] = movies['cast'].apply(get_cast)
    movies['director'] = movies['crew'].apply(get_crew)
    movies['prduction_comp'] = movies['production_companies'].apply(get_genres)

    #  Removing spaces from between the lines
    movies['overview'] = movies['overview'].apply(lambda x: x.split())
    movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tcast'] = movies['top_cast'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tcrew'] = movies['director'].apply(lambda x: [i.replace(" ", "") for i in x])
    movies['tprduction_comp'] = movies['prduction_comp'].apply(lambda x: [i.replace(" ", "") for i in x])

    # Creating a tags where we have all the words together for analysis
    movies['tags'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['tcast'] + movies['tcrew']

    #  Creating new dataframe for the analysis part only.
    new_df = movies[['movie_id', 'title', 'tags', 'genres', 'keywords', 'tcast', 'tcrew', 'tprduction_comp']]

    # new_df['tags'] = new_df['tags'].apply(lambda x: " ".join(x))
    new_df['genres'] = new_df['genres'].apply(lambda x: " ".join(x))
    # new_df['keywords'] = new_df['keywords'].apply(lambda x: " ".join(x))
    new_df['tcast'] = new_df['tcast'].apply(lambda x: " ".join(x))
    new_df['tprduction_comp'] = new_df['tprduction_comp'].apply(lambda x: " ".join(x))

    new_df['tcast'] = new_df['tcast'].apply(lambda x: x.lower())
    new_df['genres'] = new_df['genres'].apply(lambda x: x.lower())
    new_df['tprduction_comp'] = new_df['tprduction_comp'].apply(lambda x: x.lower())

    #  Applying stemming on tags and tags and keywords
    new_df['tags'] = new_df['tags'].apply(stemming_stopwords)
    new_df['keywords'] = new_df['keywords'].apply(stemming_stopwords)

    return movies, new_df, movies2


def stemming_stopwords(li):
    ans = []

    # ps = PorterStemmer()

    for i in li:
        ans.append(ps.stem(i))

    # Removing Stopwords
    stop_words = set(stopwords.words('english'))
    filtered_sentence = []
    for w in ans:
        w = w.lower()
        if w not in stop_words:
            filtered_sentence.append(w)

    str_ = ''
    for i in filtered_sentence:
        if len(i) > 2:
            str_ = str_ + i + ' '

    # Removing Punctuations
    punc = string.punctuation
    str_.translate(str_.maketrans('', '', punc))
    return str_


import os
import scipy.sparse as sp

def get_api_key():
    # 1. Try Streamlit Secrets
    try:
        if hasattr(st, "secrets") and "TMDB_API_KEY" in st.secrets:
            return st.secrets["TMDB_API_KEY"]
    except Exception:
        pass
    
    # 2. Try OS environment variable
    env_key = os.environ.get("TMDB_API_KEY")
    if env_key:
        return env_key
        
    # 3. Fallback Key
    return "6177b4297dff132d300422e0343471fb"


@st.cache_data
def fetch_posters(movie_id):
    # Lookup movie title for logging
    movie_title = "Unknown Movie"
    try:
        df = load_dataframe_from_pickle(r'Files/movies2_dict.pkl')
        row = df[df['movie_id'] == movie_id]
        if not row.empty:
            movie_title = row.iloc[0]['title']
    except Exception:
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    try:
        api_key = get_api_key()
        response = requests.get(
            'https://api.tmdb.org/3/movie/{}?api_key={}'.format(movie_id, api_key),
            headers=headers,
            timeout=5,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            if 'poster_path' in data and data['poster_path']:
                return "https://image.tmdb.org/t/p/w780/" + data['poster_path']
            else:
                print(f"[API WARN] Movie '{movie_title}' (ID: {movie_id}) has no poster path on TMDB. Response: {response.text[:200]}")
        else:
            print(f"[API ERROR] Failed to fetch poster for '{movie_title}' (ID: {movie_id}). Status: {response.status_code}. Response: {response.text[:200]}")
    except Exception as e:
        print(f"[API ERROR] Exception fetching poster for '{movie_title}' (ID: {movie_id}): {type(e).__name__} - {e}")
        
    return "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop"


@st.cache_resource
def load_sparse_matrix(file_path):
    return sp.load_npz(file_path)


def recommend(new_df, movie, npz_file_path):
    # Load cached sparse CSR matrix representation
    vec_matrix = load_sparse_matrix(npz_file_path)

    movie_idx = new_df[new_df['title'] == movie].index[0]
    
    # Extract query vector for selected movie
    query_vector = vec_matrix[movie_idx]

    # Calculate cosine similarity on-the-fly
    # query_vector is shape (1, 5000) and vec_matrix is shape (4803, 5000)
    similarity_scores = cosine_similarity(query_vector, vec_matrix)[0]

    # Getting the top 25 movies from the list which are most similar
    movie_list = sorted(list(enumerate(similarity_scores)), reverse=True, key=lambda x: x[1])[1:26]

    rec_movie_list = []
    rec_movie_ids = []
    rec_scores = []

    for i in movie_list:
        rec_movie_list.append(new_df.iloc[i[0]]['title'])
        rec_movie_ids.append(new_df.iloc[i[0]]['movie_id'])
        rec_scores.append(round(float(i[1]) * 100, 1))

    return rec_movie_list, rec_movie_ids, rec_scores


def vectorise(new_df, col_name):
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vec_tags = cv.fit_transform(new_df[col_name]).toarray()
    sim_bt = cosine_similarity(vec_tags)
    return sim_bt


@st.cache_data
def fetch_person_details(id_):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    try:
        api_key = get_api_key()
        response = requests.get(
            'https://api.tmdb.org/3/person/{}?api_key={}'.format(id_, api_key),
            headers=headers,
            timeout=5,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            url = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?q=80&w=200&auto=format&fit=crop"
            if 'profile_path' in data and data['profile_path']:
                url = 'https://image.tmdb.org/t/p/w220_and_h330_face' + data['profile_path']
            biography = data.get('biography', '') or ''
            return url, biography
        else:
            print(f"[API ERROR] Failed to fetch details for person ID {id_}. Status: {response.status_code}. Response: {response.text[:200]}")
    except Exception as e:
        print(f"[API ERROR] Exception fetching details for person ID {id_}: {type(e).__name__} - {e}")
        
    return "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?q=80&w=200&auto=format&fit=crop", ""



def get_details(selected_movie_name):
    if not selected_movie_name:
        return None

    # Loading both the dataframes for fast reading
    movies = load_dataframe_from_pickle(r'Files/movies_dict.pkl')
    movies2 = load_dataframe_from_pickle(r'Files/movies2_dict.pkl')

    # Extracting series of data to be displayed
    a = movies2[movies2['title'] == selected_movie_name]
    b = movies[movies['title'] == selected_movie_name]

    if a.empty or b.empty:
        return None

    # Extracting necessary details
    budget = a.iloc[0, 2]
    overview = a.iloc[0, 3]
    release_date = a.iloc[:, 5].iloc[0]
    revenue = a.iloc[:, 6].iloc[0]
    runtime = a.iloc[:, 7].iloc[0]
    available_lang = ast.literal_eval(a.iloc[0, 8])
    vote_rating = a.iloc[:, 10].iloc[0]
    vote_count = a.iloc[:, 11].iloc[0]
    movie_id = a.iloc[:, 0].iloc[0]
    cast = b.iloc[:, 9].iloc[0]
    director = b.iloc[:, 10].iloc[0]
    genres = b.iloc[:, 3].iloc[0]
    this_poster = fetch_posters(movie_id)
    cast_per = b.iloc[:, 5].iloc[0]
    a_cast_per = ast.literal_eval(cast_per)
    cast_id = []
    for i in a_cast_per:
        cast_id.append(i['id'])
    lang = []
    for i in available_lang:
        lang.append(i['name'])

    # Adding to a list for easy export
    info = [this_poster, budget, genres, overview, release_date, revenue, runtime, available_lang, vote_rating,
            vote_count, movie_id, cast, director, lang, cast_id]

    return info

