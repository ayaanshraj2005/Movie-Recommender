# Deploying to Streamlit Community Cloud

Follow these steps to deploy your Movie Recommender System project to [Streamlit Community Cloud](https://share.streamlit.io/).

## Prerequisites

1. A **GitHub account** containing this repository.
2. A **Streamlit Community Cloud account** (linked to your GitHub account).

---

## Deployment Steps

### Step 1: Push Changes to GitHub
Make sure all your local files are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Fix crashes, add caching and optimize app health"
git push origin main
```

### Step 2: Set Up Streamlit Cloud
1. Log in to [Streamlit Share](https://share.streamlit.io/).
2. Click the **"New app"** button.

### Step 3: Configure Deployment Details
- **Repository:** Select your `Movie-Recommender-System` repository.
- **Branch:** `main` (or whichever branch you pushed to).
- **Main file path:** `main.py`

### Step 4: Add Secrets (Optional but Recommended)
If you decide to externalize your TMDB API Key:
1. In the app settings on Streamlit Cloud, go to **Secrets**.
2. Add your secret key:
   ```toml
   TMDB_API_KEY = "6177b4297dff132d300422e0343471fb"
   ```
3. Update `preprocess.py` to retrieve it:
   ```python
   api_key = st.secrets["TMDB_API_KEY"]
   ```

### Step 5: Deploy
Click **"Deploy!"**. Streamlit will provision a container, install dependencies from `requirements.txt` (using the version specified in `runtime.txt`), download stopwords via NLTK, and run your app.

---

## Cloud Environment Optimization Notes
- **Memory Limit:** Streamlit Community Cloud has a memory limit of **1 GB**.
- **Pickle Files:** The project loads ~900MB of pickle files. Because of the `@st.cache_resource` memory optimization we implemented, the files are only loaded once. This stays safely within the 1 GB limits.
