import os
from processing import preprocess
import pickle
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Main():

    def __enter__(self):
        # Initialization code, if needed
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Cleanup code, if needed
        pass

    def __init__(self):
        self.new_df = None
        self.movies = None
        self.movies2 = None

    def getter(self):
        return self.new_df, self.movies, self.movies2

    def get_df(self):
        pickle_file_path = r'Files/new_df_dict.pkl'

        # Checking if preprocessed dataframe already exists or not
        if os.path.exists(pickle_file_path):

            # Read the Pickle file and load the dictionary -- 3 times using cached helper
            self.movies = preprocess.load_dataframe_from_pickle(r'Files/movies_dict.pkl')
            self.movies2 = preprocess.load_dataframe_from_pickle(r'Files/movies2_dict.pkl')
            self.new_df = preprocess.load_dataframe_from_pickle(r'Files/new_df_dict.pkl')

        else:
            self.movies, self.new_df, self.movies2 = preprocess.read_csv_to_df()
            self.movies.reset_index(drop=True, inplace=True)
            self.new_df.reset_index(drop=True, inplace=True)
            self.movies2.reset_index(drop=True, inplace=True)

            # Converting to pickle file (dumping file)
            # Convert the DataFrame to a dictionary

            #  Now, doing for the movies dataframe
            movies_dict = self.movies.to_dict()

            pickle_file_path = r'Files/movies_dict.pkl'
            with open(pickle_file_path, 'wb') as pickle_file:
                pickle.dump(movies_dict, pickle_file)

            #  Now, doing for the movies2 dataframe
            movies2_dict = self.movies2.to_dict()

            pickle_file_path = r'Files/movies2_dict.pkl'
            with open(pickle_file_path, 'wb') as pickle_file:
                pickle.dump(movies2_dict, pickle_file)

            # For the new_df
            df_dict = self.new_df.to_dict()

            # Save the dictionary to a Pickle file
            pickle_file_path = r'Files/new_df_dict.pkl'
            with open(pickle_file_path, 'wb') as pickle_file:
                pickle.dump(df_dict, pickle_file)

    def vectorise(self, col_name):
        # Model to vectorise the words using CountVectorizer (Bag of words)
        cv = CountVectorizer(max_features=5000, stop_words='english')
        vec_tags = cv.fit_transform(self.new_df[col_name]).toarray()
        sim_bt = cosine_similarity(vec_tags)
        return sim_bt

    def get_similarity(self, col_name):
        import scipy.sparse as sp
        npz_file_path = fr'Files/vectorized_{col_name}.npz'
        if os.path.exists(npz_file_path):
            pass
        else:
            cv = CountVectorizer(max_features=5000, stop_words='english')
            vec_sparse = cv.fit_transform(self.new_df[col_name])
            sp.save_npz(npz_file_path, vec_sparse)

    def main_(self):
        # This is to make sure that resources are available.
        self.get_df()
        self.get_similarity('tags')
        self.get_similarity('genres')
        self.get_similarity('keywords')
        self.get_similarity('tcast')
        self.get_similarity('tprduction_comp')