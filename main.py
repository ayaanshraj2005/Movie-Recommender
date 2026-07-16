import streamlit as st
import streamlit_option_menu
from streamlit_extras.stoggle import stoggle
from processing import preprocess
from processing.display import Main

# Setting the wide mode as default
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def local_css(file_name):
    try:
        with open(file_name, "r") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception:
        pass

local_css("assets/style.css")

displayed = []

if 'movie_number' not in st.session_state:
    st.session_state['movie_number'] = 0

if 'selected_movie_name' not in st.session_state:
    st.session_state['selected_movie_name'] = ""

if 'user_menu' not in st.session_state:
    st.session_state['user_menu'] = ""


def main():
    def initial_options():
        # To display menu
        st.session_state.user_menu = streamlit_option_menu.option_menu(
            menu_title='What are you looking for? 👀',
            options=['Recommend me a similar movie', 'Describe me a movie', 'Check all Movies'],
            icons=['film', 'film', 'film'],
            menu_icon='list',
            orientation="horizontal",
        )

        if st.session_state.user_menu == 'Recommend me a similar movie':
            recommend_display()

        elif st.session_state.user_menu == 'Describe me a movie':
            display_movie_details()

        elif st.session_state.user_menu == 'Check all Movies':
            paging_movies()

    def recommend_display():

        st.title('Movie Recommender System 🎬')

        selected_movie_name = st.selectbox(
            'Select a Movie...', new_df['title'].values
        )

        rec_button = st.button('Recommend')
        if rec_button:
            displayed.clear()
            st.session_state.selected_movie_name = selected_movie_name
            with st.spinner("Generating recommendations from different perspectives... 🔮"):
                # Define configurations for different recommendation perspectives
                perspectives = [
                    (r'Files/vectorized_tags.npz', "are"),
                    (r'Files/vectorized_genres.npz', "on the basis of genres are"),
                    (r'Files/vectorized_tprduction_comp.npz', "from the same production company are"),
                    (r'Files/vectorized_keywords.npz', "on the basis of keywords are"),
                    (r'Files/vectorized_tcast.npz', "on the basis of cast are")
                ]
                
                computed_results = []
                unique_ids_to_fetch = set()
                
                # Compute matches first (fast scipy operations)
                for npz_file_path, str_text in perspectives:
                    movies, movie_ids, scores = preprocess.recommend(new_df, selected_movie_name, npz_file_path)
                    
                    rec_movies = []
                    rec_ids = []
                    rec_scores = []
                    cnt = 0
                    for i, j in enumerate(movies):
                        if cnt == 5:
                            break
                        if j not in displayed:
                            rec_movies.append(j)
                            rec_ids.append(movie_ids[i])
                            rec_scores.append(scores[i])
                            displayed.append(j)
                            unique_ids_to_fetch.add(movie_ids[i])
                            cnt += 1
                    computed_results.append((str_text, rec_movies, rec_ids, rec_scores))
                
                # Fetch all unique posters in parallel
                from concurrent.futures import ThreadPoolExecutor
                unique_ids_list = list(unique_ids_to_fetch)
                with ThreadPoolExecutor(max_workers=15) as executor:
                    posters_list = list(executor.map(preprocess.fetch_posters, unique_ids_list))
                
                poster_map = dict(zip(unique_ids_list, posters_list))
                
                # Render results categories
                for str_text, rec_movies, rec_ids, rec_scores in computed_results:
                    st.write(f'#### Best Recommendations {str_text}...')
                    cols = st.columns(5)
                    for idx in range(min(5, len(rec_movies))):
                        m_id = rec_ids[idx]
                        poster_url = poster_map.get(m_id, "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop")
                        with cols[idx]:
                            card_html = f"""
                            <div class="movie-card">
                                <div class="movie-poster-container">
                                    <span class="match-badge">{rec_scores[idx]}% Match</span>
                                    <img class="movie-poster" src="{poster_url}" alt="{rec_movies[idx]}" />
                                </div>
                                <div class="movie-card-title">{rec_movies[idx]}</div>
                            </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                    st.write("")

    def display_movie_details():

        selected_movie_name = st.session_state.selected_movie_name
        if not selected_movie_name:
            st.warning("Please go to 'Recommend me a similar movie' and select a movie first!")
            return

        with st.spinner("Fetching movie details... 🎬"):
            info = preprocess.get_details(selected_movie_name)
        if info is None:
            st.error("Movie details not found.")
            return

        # Formatting values safely
        rating = f"⭐ {info[8]:.1f} / 10" if info[8] else "N/A"
        votes = f"({info[9]:,} votes)" if info[9] else ""
        runtime = f"🕒 {info[6]} min" if info[6] else "N/A"
        release_date = f"📅 {info[4]}" if info[4] else "N/A"
        language = f"🗣️ {', '.join(info[13])}" if info[13] else "N/A"
        budget = f"💰 ${info[1]:,}" if (info[1] and info[1] > 0) else "💰 N/A"
        revenue = f"📈 ${info[5]:,}" if (info[5] and info[5] > 0) else "📈 N/A"
        director = info[12][0] if (info[12] and len(info[12]) > 0) else "N/A"
        genre_tags = "".join([f'<span class="genre-tag">{g}</span>' for g in info[2]])

        with st.container():
            image_col, text_col = st.columns((1, 2))
            with image_col:
                st.write("")
                st.markdown(
                    f"""
                    <div style="border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1);">
                        <img src="{info[0]}" style="width: 100%; display: block;" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with text_col:
                st.write("")
                st.markdown(f"<h1 style='margin-bottom: 0px;'>{selected_movie_name}</h1>", unsafe_allow_html=True)
                st.markdown(f"<p style='color: #a78bfa; font-weight: 500; font-size: 1.1rem; margin-top: 5px;'>Directed by {director} &nbsp;|&nbsp; 100% Match (Current Movie)</p>", unsafe_allow_html=True)
                
                # Genre tags
                st.markdown(f'<div class="genre-container" style="margin-bottom: 20px;">{genre_tags}</div>', unsafe_allow_html=True)
                
                # Detail Grid
                st.markdown(
                    f"""
                    <div class="detail-grid">
                        <div class="detail-pill">
                            <div class="detail-pill-label">Rating</div>
                            <div class="detail-pill-val">{rating}</div>
                            <div style="font-size: 0.75rem; color: #9ca3af;">{votes}</div>
                        </div>
                        <div class="detail-pill">
                            <div class="detail-pill-label">Runtime</div>
                            <div class="detail-pill-val">{runtime}</div>
                        </div>
                        <div class="detail-pill">
                            <div class="detail-pill-label">Release Date</div>
                            <div class="detail-pill-val">{release_date}</div>
                        </div>
                        <div class="detail-pill">
                            <div class="detail-pill-label">Language</div>
                            <div class="detail-pill-val">{language}</div>
                        </div>
                        <div class="detail-pill">
                            <div class="detail-pill-label">Budget</div>
                            <div class="detail-pill-val">{budget}</div>
                        </div>
                        <div class="detail-pill">
                            <div class="detail-pill-label">Revenue</div>
                            <div class="detail-pill-val">{revenue}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.write("### Overview")
                st.write(info[3])
                st.write("")

        # Displaying information of casts.
        st.write("---")
        st.write("### Top Cast")
        cnt = 0
        cast_names = []
        cast_ids_to_fetch = []
        for idx, i in enumerate(info[14]):
            if cnt == 5:
                break
            cast_ids_to_fetch.append(i)
            cast_names.append(info[11][idx] if idx < len(info[11]) else "Unknown Actor")
            cnt += 1

        urls = []
        bio = []
        with st.spinner("Loading cast details... 🎭"):
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:
                cast_details = list(executor.map(preprocess.fetch_person_details, cast_ids_to_fetch))
            
            for url, biography in cast_details:
                urls.append(url)
                bio.append(biography)

        cols = st.columns(5)
        for idx in range(min(5, len(urls))):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div style="text-align: center; margin-bottom: 12px;">
                        <img src="{urls[idx]}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 50%; border: 2px solid rgba(139, 92, 246, 0.4); box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 8px;" />
                        <div style="font-weight: 600; font-size: 0.95rem; color: #ffffff; line-height: 1.2; min-height: 2.4rem; display: flex; align-items: center; justify-content: center;">{cast_names[idx]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                # Toggle button to show information of cast.
                stoggle(
                    "Show Bio",
                    bio[idx] if bio[idx] else "Biography not available.",
                )

    def paging_movies():
        # To create pages functionality using session state.
        max_pages = movies.shape[0] / 10
        max_pages = int(max_pages) - 1

        col1, col2, col3 = st.columns([1, 9, 1])

        with col1:
            st.text("Previous page")
            prev_btn = st.button("Prev")
            if prev_btn:
                if st.session_state['movie_number'] >= 10:
                    st.session_state['movie_number'] -= 10

        with col2:
            new_page_number = st.slider("Jump to page number", 0, max_pages, st.session_state['movie_number'] // 10)
            st.session_state['movie_number'] = new_page_number * 10

        with col3:
            st.text("Next page")
            next_btn = st.button("Next")
            if next_btn:
                if st.session_state['movie_number'] + 10 < len(movies):
                    st.session_state['movie_number'] += 10

        display_all_movies(st.session_state['movie_number'])

    def display_all_movies(start):

        i = start
        movie_ids_to_fetch = []
        for offset in range(10):
            if start + offset < len(movies):
                movie_ids_to_fetch.append(movies.iloc[start + offset]['movie_id'])

        with st.spinner("Loading posters... 🎬"):
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=10) as executor:
                posters = list(executor.map(preprocess.fetch_posters, movie_ids_to_fetch))
        
        poster_map = dict(zip(movie_ids_to_fetch, posters))

        # Row 1
        with st.container():
            cols = st.columns(5)
            for idx in range(5):
                if i >= len(movies):
                    break
                row = movies.iloc[i]
                id = row['movie_id']
                link = poster_map.get(id, "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop")
                with cols[idx]:
                    card_html = f"""
                    <div class="movie-card">
                        <div class="movie-poster-container">
                            <img class="movie-poster" src="{link}" alt="{row['title']}" />
                        </div>
                        <div class="movie-card-title">{row['title']}</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                i = i + 1
            st.write("")

        # Row 2
        with st.container():
            cols = st.columns(5)
            for idx in range(5):
                if i >= len(movies):
                    break
                row = movies.iloc[i]
                id = row['movie_id']
                link = poster_map.get(id, "https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=500&auto=format&fit=crop")
                with cols[idx]:
                    card_html = f"""
                    <div class="movie-card">
                        <div class="movie-poster-container">
                            <img class="movie-poster" src="{link}" alt="{row['title']}" />
                        </div>
                        <div class="movie-card-title">{row['title']}</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                i = i + 1
            st.write("")

        st.session_state['page_number'] = i

    with Main() as bot:
        bot.main_()
        new_df, movies, movies2 = bot.getter()
        initial_options()


if __name__ == '__main__':
    main()
