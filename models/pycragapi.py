import json
import os
import pandas as pd
import numpy as np
from typing import List

class CRAG(object):
    def __init__(self):
        print("\n" + "="*50)
        print("[DEBUG] INITIALIZING OFFLINE DATABASE ENGINE (FULL LOAD)")
        print("="*50)
        self.data_dir = "models/processed_data"
        
        def safe_load(filename):
            path = os.path.join(self.data_dir, filename)
            if not os.path.exists(path):
                print(f"[DEBUG] NOT FOUND: {filename}")
                return None
            try:
                if filename.endswith('.csv'):
                    data = pd.read_csv(path)
                    print(f"[DEBUG] LOADED CSV: {filename} ({len(data)} rows)")
                    return data
                elif filename.endswith('.npy'):
                    data = np.load(path, allow_pickle=True)
                    if data.ndim == 0:
                        data = data.item()
                    print(f"[DEBUG] LOADED NPY: {filename} (Type: {type(data)})")
                    return data
            except Exception as e:
                print(f"[DEBUG] ERROR LOADING {filename}: {e}")
                return None

        # Memuat seluruh dataset riset
        self.oscar_df = safe_load("the_oscar_award.csv")
        self.grammy_df = safe_load("the_grammy_awards.csv")
        self.grammy_songs_df = safe_load("grammySongs_1999-2019.csv")
        self.finance_data = safe_load("finance_data.npy")
        self.imdb_movies = safe_load("imdb_movie_dataset.npy")
        self.all_imdb_movie = safe_load("all_imdb_movie.npy")
        self.grammy_map = safe_load("grammy.npy")
        self.oscar_map = safe_load("oscar_map.npy")
        self.oscar_map_dlc = safe_load("oscar_map_dlc.npy")
        self.stopwords_list = safe_load("stopwords_list.npy")
        print("="*50 + "\n")

    def _empty(self): return {"result": []}

    def movie_get_movie_info(self, movie_name: str):
        query = str(movie_name).lower().strip()
        if isinstance(self.imdb_movies, dict):
            results = [v for k, v in self.imdb_movies.items() if query in str(k).lower()]
            return {"result": results}
        return self._empty()

    def movie_get_year_info(self, year: str):
        if self.oscar_df is not None:
            df = self.oscar_df[self.oscar_df['year_ceremony'] == int(year)].copy()
            return {"result": {"oscar_awards": df.to_dict('records'), "movie_list": []}}
        return self._empty()

    def finance_get_ticker_by_name(self, query: str):
        if isinstance(self.finance_data, dict):
            return {"result": [k for k in self.finance_data.keys() if str(query).upper() in str(k)]}
        return self._empty()

    def finance_get_market_capitalization(self, ticker: str):
        if isinstance(self.finance_data, dict):
            val = self.finance_data.get(ticker.upper(), {}).get('market_cap', [])
            return {"result": [val] if val else []}
        return self._empty()
    
    # Stub untuk fungsi lainnya agar tidak crash
    def open_get_entity(self, e): return self._empty()
    def sports_soccer_get_games_on_date(self, d, t): return self._empty()
    def music_get_artist_all_works(self, n): return self._empty()