import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from contextlib import contextmanager
import os

# Page configuration
st.set_page_config(
    page_title="Streaming Content Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== PROFESSIONAL STYLING ====================

st.markdown("""
    <style>
    /* Clean dark background */
    .stApp {
        background-color: #0f1116;
    }
    
    .main {
        background-color: #0f1116;
    }
    
    /* Professional header - subtle and clean */
    .dashboard-header {
        color: #ffffff;
        font-size: 2.5rem;
        font-weight: 600;
        text-align: left;
        margin-bottom: 0.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #2a2d35;
        letter-spacing: -0.01em;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .dashboard-header-accent {
        color: #E50914;
    }
    
    /* Section headers - clean and spaced */
    .section-header {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2.5rem;
        margin-bottom: 1.25rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #2a2d35;
    }
    
    .subsection-header {
        color: #e0e0e0;
        font-size: 1.1rem;
        font-weight: 500;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* Table styling - clean and subtle */
    .stDataFrame {
        background-color: #1a1d23;
        border: 1px solid #2a2d35;
        border-radius: 6px;
    }
    
    /* Sidebar - clean and minimal */
    .stSidebar {
        background-color: #1a1d23;
    }
    
    .stSidebar .stMarkdown {
        color: #b0b0b0;
    }
    
    /* Filter labels */
    .stSidebar label {
        color: #d0d0d0;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Slider styling - subtle */
    .stSlider > div > div > div {
        background-color: #2a2d35;
    }
    
    .stSlider > div > div > div > div {
        background-color: #E50914;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {
        background-color: #1a1d23;
        color: #ffffff;
        border: 1px solid #2a2d35;
    }
    
    /* Text colors */
    p, .stMarkdown {
        color: #d0d0d0;
    }
    
    /* Dividers */
    hr {
        border-color: #2a2d35;
        margin: 2rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Container spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #E50914;
        font-weight: 600;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b0b0b0;
    }
    
    /* Developer Section Styling */
    .developer-section {
        background-color: #1a1d23;
        border-top: 1px solid #2a2d35;
        padding: 2.5rem 1rem;
        margin-top: 3rem;
        text-align: center;
    }
    
    .developer-heading {
        color: #b0b0b0;
        font-size: 0.9rem;
        font-weight: 500;
        margin-bottom: 1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    .developer-name {
        color: #d0d0d0;
        font-size: 1.1rem;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    
    .developer-links {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    
    .developer-link {
        color: #8a8a8a;
        text-decoration: none;
        font-size: 1.5rem;
        transition: all 0.3s ease;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 4px;
    }
    
    .developer-link:hover {
        color: #E50914;
        transform: translateY(-2px);
    }
    
    .developer-link-icon {
        font-size: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .developer-links {
            gap: 1.5rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

# ==================== DATABASE PATH DETECTION ====================

def find_database():
    """Find the database file in common locations."""
    possible_paths = [
        "netflix.db",
        os.path.join(os.path.dirname(__file__), "netflix.db"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return "netflix.db"

DB_PATH = find_database()

# ==================== DATABASE CONNECTION ====================

@contextmanager
def get_db_connection():
    """Create and manage SQLite database connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

# ==================== QUERY FUNCTIONS ====================

@st.cache_data
def get_year_range():
    """Get minimum and maximum release years from database."""
    query = """
    SELECT MIN(release_year) as min_year, MAX(release_year) as max_year
    FROM titles
    WHERE release_year IS NOT NULL
    """
    with get_db_connection() as conn:
        result = pd.read_sql_query(query, conn)
        min_year = result['min_year'].iloc[0]
        max_year = result['max_year'].iloc[0]
        
        if pd.isna(min_year) or min_year is None:
            min_year = 1900
        if pd.isna(max_year) or max_year is None:
            max_year = 2024
        
        return int(min_year), int(max_year)

@st.cache_data
def get_top_movies(limit=10, year_min=None, year_max=None, min_imdb=None):
    """Get top movies by IMDB score."""
    conditions = ["UPPER(type) = 'MOVIE'", "imdb_score IS NOT NULL"]
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT title, imdb_score, release_year
    FROM titles
    WHERE {where_clause}
    ORDER BY imdb_score DESC
    LIMIT {limit}
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_bottom_movies(limit=10, year_min=None, year_max=None, min_imdb=None):
    """Get bottom movies by IMDB score."""
    conditions = ["UPPER(type) = 'MOVIE'", "imdb_score IS NOT NULL"]
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT title, imdb_score, release_year
    FROM titles
    WHERE {where_clause}
    ORDER BY imdb_score ASC
    LIMIT {limit}
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_top_shows(limit=10, year_min=None, year_max=None, min_imdb=None):
    """Get top shows by IMDB score."""
    conditions = ["UPPER(type) = 'SHOW'", "imdb_score IS NOT NULL"]
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT title, imdb_score, release_year
    FROM titles
    WHERE {where_clause}
    ORDER BY imdb_score DESC
    LIMIT {limit}
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_bottom_shows(limit=10, year_min=None, year_max=None, min_imdb=None):
    """Get bottom shows by IMDB score."""
    conditions = ["UPPER(type) = 'SHOW'", "imdb_score IS NOT NULL"]
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT title, imdb_score, release_year
    FROM titles
    WHERE {where_clause}
    ORDER BY imdb_score ASC
    LIMIT {limit}
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_production_countries_data(year_min=None, year_max=None, min_imdb=None, content_type=None):
    """Get production countries data for map visualization."""
    conditions = []
    
    if content_type and content_type != "All":
        if content_type == "Movie":
            conditions.append("UPPER(type) = 'MOVIE'")
        else:
            conditions.append("UPPER(type) = 'SHOW'")
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        production_countries,
        COUNT(*) as count
    FROM titles
    WHERE production_countries IS NOT NULL 
    AND production_countries != ''
    AND production_countries != '[]'
    AND {where_clause}
    GROUP BY production_countries
    ORDER BY count DESC
    LIMIT 50
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_decade_data(year_min=None, year_max=None, min_imdb=None, content_type=None):
    """Get movies and shows count by decade."""
    conditions = []
    
    if content_type and content_type != "All":
        if content_type == "Movie":
            conditions.append("UPPER(type) = 'MOVIE'")
        else:
            conditions.append("UPPER(type) = 'SHOW'")
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        (FLOOR(release_year / 10) * 10) as decade,
        type,
        COUNT(*) as count
    FROM titles
    WHERE release_year IS NOT NULL
    AND release_year >= 1940
    AND {where_clause}
    GROUP BY decade, type
    ORDER BY decade
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_age_certification_data(year_min=None, year_max=None, min_imdb=None, content_type=None):
    """Get top age certifications."""
    conditions = [
        "age_certification IS NOT NULL", 
        "age_certification != ''", 
        "age_certification != 'N/A'"
    ]
    
    if content_type and content_type != "All":
        if content_type == "Movie":
            conditions.append("UPPER(type) = 'MOVIE'")
        else:
            conditions.append("UPPER(type) = 'SHOW'")
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        age_certification,
        COUNT(*) as count
    FROM titles
    WHERE {where_clause}
    GROUP BY age_certification
    ORDER BY count DESC
    LIMIT 5
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_top_seasons_shows(limit=10, year_min=None, year_max=None, min_imdb=None):
    """Get top shows by number of seasons."""
    conditions = ["UPPER(type) = 'SHOW'", "seasons IS NOT NULL"]
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions)
    
    query = f"""
    SELECT 
        title,
        SUM(seasons) as total_seasons,
        release_year
    FROM titles
    WHERE {where_clause}
    GROUP BY title
    ORDER BY total_seasons DESC
    LIMIT {limit}
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

@st.cache_data
def get_avg_scores_by_type(year_min=None, year_max=None, min_imdb=None):
    """Get average IMDB and TMDB scores by content type."""
    conditions = []
    
    if year_min:
        conditions.append(f"release_year >= {year_min}")
    if year_max:
        conditions.append(f"release_year <= {year_max}")
    if min_imdb and min_imdb > 0:
        conditions.append(f"imdb_score >= {min_imdb}")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        type,
        ROUND(AVG(imdb_score), 2) as avg_imdb_score,
        ROUND(AVG(tmdb_score), 2) as avg_tmdb_score
    FROM titles
    WHERE imdb_score IS NOT NULL
    AND tmdb_score IS NOT NULL
    AND {where_clause}
    GROUP BY type
    """
    with get_db_connection() as conn:
        return pd.read_sql_query(query, conn)

# ==================== HELPER FUNCTIONS ====================

def style_dataframe_with_heatmap(df, score_col='IMDb Score'):
    """Apply subtle heat-style coloring only to score column."""
    if df.empty or score_col not in df.columns:
        return df.style
    
    # Normalize scores for color mapping
    min_score = df[score_col].min()
    max_score = df[score_col].max()
    score_range = max_score - min_score if max_score != min_score else 1
    
    def get_color(val):
        """Get subtle red gradient color based on score."""
        if pd.isna(val):
            return 'background-color: #1a1d23; color: #d0d0d0;'
        normalized = (val - min_score) / score_range
        # Subtle gradient from dark to bright red
        r = int(100 + (normalized * 155))  # 64 to E5
        g = int(9 + (normalized * 0))
        b = int(20 + (normalized * 0))
        return f'background-color: rgb({r}, {g}, {b}); color: #ffffff; font-weight: 500;'
    
    # Apply styling only to score column
    styled = df.style.applymap(
        get_color,
        subset=[score_col]
    ).format({
        score_col: '{:.2f}',
        'Year': '{:.0f}'
    }).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1a1d23'), ('color', '#d0d0d0'), ('border', '1px solid #2a2d35')]},
        {'selector': 'td', 'props': [('background-color', '#1a1d23'), ('color', '#d0d0d0'), ('border', '1px solid #2a2d35')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#252830')]}
    ])
    
    return styled

# ==================== MAIN DASHBOARD ====================

# Professional Header with proper spacing
st.markdown(
    '<div class="dashboard-header">Streaming <span class="dashboard-header-accent">Content Analytics</span> Dashboard</div>',
    unsafe_allow_html=True
)

# Get year range
try:
    min_year, max_year = get_year_range()
except:
    min_year, max_year = 1900, 2024

# Sidebar Filters - Clean and Minimal
with st.sidebar:
    st.markdown("### Filters")
    st.markdown("---")
    
    content_type = st.selectbox(
        "Content Type",
        options=["All", "Movie", "Show"],
        index=0,
        help="Filter by content type"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    year_range = st.slider(
        "Release Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
        help="Select year range for filtering"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    min_imdb = st.slider(
        "Minimum IMDb Score",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        help="Filter by minimum IMDb rating"
    )

# Get filtered data
top_movies = get_top_movies(10, year_range[0], year_range[1], min_imdb if min_imdb > 0 else None)
bottom_movies = get_bottom_movies(10, year_range[0], year_range[1], min_imdb if min_imdb > 0 else None)
top_shows = get_top_shows(10, year_range[0], year_range[1], min_imdb if min_imdb > 0 else None)
bottom_shows = get_bottom_shows(10, year_range[0], year_range[1], min_imdb if min_imdb > 0 else None)

# ==================== RANKING TABLES SECTION ====================

st.markdown('<div class="section-header">Content Rankings by IMDb Score</div>', unsafe_allow_html=True)

# Four tables in clean horizontal layout with proper spacing
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.markdown("**Top 10 Movies**")
    if not top_movies.empty:
        display_df = top_movies[['title', 'imdb_score', 'release_year']].copy()
        display_df.columns = ['Title', 'IMDb Score', 'Year']
        display_df.index = range(1, len(display_df) + 1)
        styled = style_dataframe_with_heatmap(display_df, 'IMDb Score')
        st.dataframe(styled, use_container_width=True, height=380, hide_index=False)
    else:
        st.info("No data available")

with col2:
    st.markdown("**Top 10 TV Shows**")
    if not top_shows.empty:
        display_df = top_shows[['title', 'imdb_score', 'release_year']].copy()
        display_df.columns = ['Title', 'IMDb Score', 'Year']
        display_df.index = range(1, len(display_df) + 1)
        styled = style_dataframe_with_heatmap(display_df, 'IMDb Score')
        st.dataframe(styled, use_container_width=True, height=380, hide_index=False)
    else:
        st.info("No data available")

with col3:
    st.markdown("**Bottom 10 Movies**")
    if not bottom_movies.empty:
        display_df = bottom_movies[['title', 'imdb_score', 'release_year']].copy()
        display_df.columns = ['Title', 'IMDb Score', 'Year']
        display_df.index = range(1, len(display_df) + 1)
        styled = style_dataframe_with_heatmap(display_df, 'IMDb Score')
        st.dataframe(styled, use_container_width=True, height=380, hide_index=False)
    else:
        st.info("No data available")

with col4:
    st.markdown("**Bottom 10 TV Shows**")
    if not bottom_shows.empty:
        display_df = bottom_shows[['title', 'imdb_score', 'release_year']].copy()
        display_df.columns = ['Title', 'IMDb Score', 'Year']
        display_df.index = range(1, len(display_df) + 1)
        styled = style_dataframe_with_heatmap(display_df, 'IMDb Score')
        st.dataframe(styled, use_container_width=True, height=380, hide_index=False)
    else:
        st.info("No data available")

# ==================== DEVELOPER SECTION ====================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")

# Developer Section
st.markdown("""
    <div class="developer-section">
        <div class="developer-heading">Know the Developer</div>
        <div class="developer-name">Abhinav</div>
        <div class="developer-links">
            <a href="https://github.com/abhinav4568482" target="_blank" rel="noopener noreferrer" class="developer-link" title="GitHub">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                </svg>
            </a>
            <a href="https://www.linkedin.com/in/avinvxsingh" target="_blank" rel="noopener noreferrer" class="developer-link" title="LinkedIn">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
            </a>
            <a href="https://folioavinv.netlify.app/" target="_blank" rel="noopener noreferrer" class="developer-link" title="Portfolio">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                    <line x1="12" y1="22.08" x2="12" y2="12"></line>
                </svg>
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)
