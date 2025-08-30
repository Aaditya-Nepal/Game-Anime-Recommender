from __future__ import annotations

import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from difflib import get_close_matches
import threading
import time
try:
    import requests  # type: ignore
except Exception:
    requests = None

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
ANIME_DIR = os.path.join(APP_ROOT, "Anime")
GAMES_DIR = os.path.join(APP_ROOT, "Game")
ANIME_IMG_CACHE_PATH = os.path.join(APP_ROOT, "anime_image_cache.json")

# Global trained models
TRAINED_MODELS = {}

# in-memory cache for anime covers
_anime_img_cache_lock = threading.Lock()
try:
    if os.path.exists(ANIME_IMG_CACHE_PATH):
        with open(ANIME_IMG_CACHE_PATH, "r", encoding="utf-8") as _f:
            ANIME_IMG_CACHE: Dict[str, str] = json.load(_f)
    else:
        ANIME_IMG_CACHE = {}
except Exception:
    ANIME_IMG_CACHE = {}


def _safe_load_pickle(path: str, timeout: int = 30) -> Any:
    """Load pickle file with timeout to prevent hanging on large files"""
    import threading
    import queue
    
    def load_pickle_with_timeout(path: str, result_queue: queue.Queue, error_queue: queue.Queue):
        try:
            with open(path, "rb") as f:
                result = pickle.load(f)
            result_queue.put(result)
        except Exception as e:
            error_queue.put(e)
    
    try:
        result_queue = queue.Queue()
        error_queue = queue.Queue()
        
        # Start loading in a separate thread
        thread = threading.Thread(target=load_pickle_with_timeout, args=(path, result_queue, error_queue))
        thread.daemon = True
        thread.start()
        
        # Wait for result with timeout
        thread.join(timeout)
        
        if thread.is_alive():
            print(f"Warning: Loading {path} timed out after {timeout} seconds, skipping...")
            return None
        
        if not error_queue.empty():
            error = error_queue.get()
            print(f"Warning: Could not load {path}: {error}")
            return None
        
        if not result_queue.empty():
            return result_queue.get()
        
        return None
        
    except Exception as e:
        print(f"Warning: Could not load {path}: {e}")
        return None


def _load_trained_models() -> Dict[str, Dict[str, Any]]:
    """Load the trained models and data from pickle files"""
    models = {"anime": {}, "game": {}}
    
    # Load anime models
    anime_pop_path = os.path.join(ANIME_DIR, "popular.PC")
    anime_data_path = os.path.join(ANIME_DIR, "anime.awc")
    
    # Load game models
    game_pop_path = os.path.join(GAMES_DIR, "popular.PG")
    game_data_path = os.path.join(GAMES_DIR, "games.gkm")
    
    try:
        # Load only essential data - skip very large files
        if os.path.exists(anime_pop_path):
            print("Loading anime popular data...")
            models["anime"]["popular"] = _safe_load_pickle(anime_pop_path, timeout=60)
        if os.path.exists(anime_data_path):
            print("Loading anime data...")
            models["anime"]["data"] = _safe_load_pickle(anime_data_path, timeout=60)
        
        # Skip pivot table and similarity scores (too large)
        print("Skipping large anime pivot table and similarity scores...")
        
        if os.path.exists(game_pop_path):
            print("Loading game popular data...")
            models["game"]["popular"] = _safe_load_pickle(game_pop_path, timeout=60)
        if os.path.exists(game_data_path):
            print("Loading game data...")
            models["game"]["data"] = _safe_load_pickle(game_data_path, timeout=60)
        
        # Skip pivot table and similarity scores (too large)
        print("Skipping large game pivot table and similarity scores...")
            
    except Exception as e:
        print(f"Error loading models: {e}")
    
    return models


def _get_recommendations_from_trained_model(title: str, item_type: str, limit: int = 12) -> List[Dict[str, Any]]:
    """Get recommendations using the trained collaborative filtering models"""
    if item_type not in TRAINED_MODELS:
        return []
    
    models = TRAINED_MODELS[item_type]
    data = models.get("data")
    
    if data is None:
        return []
    
    try:
        results = []
        title_lower = title.lower().strip()
        
        if not title_lower:
            # If no search term, return popular items
            return _get_popular_items(item_type, limit)
        
        # Search for items with similar titles - improved accuracy
        for col in ['Name', 'name', 'title', 'Title']:
            if col in data.columns:
                # Strategy 1: Exact matches first (highest priority)
                exact_matches = data[data[col].str.lower() == title_lower]
                if not exact_matches.empty:
                    for idx, item in exact_matches.head(limit).iterrows():
                        results.append(_format_item(item, item_type, col, idx))
                
                # Strategy 2: Starts with matches (high priority)
                starts_with_matches = data[data[col].str.lower().str.startswith(title_lower, na=False)]
                if not starts_with_matches.empty:
                    for idx, item in starts_with_matches.head(limit//2).iterrows():
                        if len(results) >= limit:
                            break
                        # Avoid duplicates
                        if not any(r['title'] == str(item[col]) for r in results):
                            results.append(_format_item(item, item_type, col, idx))
                
                # Strategy 3: Contains matches (medium priority) - only if query is long enough
                if len(title_lower) >= 4:  # Only search contains for queries 4+ characters
                    contains_matches = data[data[col].str.lower().str.contains(title_lower, na=False, regex=False)]
                    if not contains_matches.empty:
                        for idx, item in contains_matches.head(limit//3).iterrows():
                            if len(results) >= limit:
                                break
                            # Avoid duplicates
                            if not any(r['title'] == str(item[col]) for r in results):
                                results.append(_format_item(item, item_type, col, idx))
                
                # Strategy 4: Word boundary matches (lower priority) - only for multi-word queries
                words = title_lower.split()
                if len(words) > 1:  # Only for multi-word queries
                    for word in words:
                        if len(word) >= 3:  # Only search for words 3+ characters
                            word_matches = data[data[col].str.lower().str.contains(r'\b' + word + r'\b', na=False, regex=True)]
                            if not word_matches.empty:
                                for idx, item in word_matches.head(limit//4).iterrows():
                                    if len(results) >= limit:
                                        break
                                    # Avoid duplicates
                                    if not any(r['title'] == str(item[col]) for r in results):
                                        results.append(_format_item(item, item_type, col, idx))
                
                break  # Found a valid column, no need to check others
        
        # If we don't have enough results, add some popular items
        if len(results) < limit:
            popular_items = _get_popular_items(item_type, limit - len(results))
            # Avoid duplicates
            existing_titles = {r['title'] for r in results}
            for item in popular_items:
                if item['title'] not in existing_titles:
                    results.append(item)
                    existing_titles.add(item['title'])
                if len(results) >= limit:
                    break
        
        return results[:limit]
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        # Fallback to popular items
        return _get_popular_items(item_type, limit)


def _format_item(item, item_type: str, col: str, idx) -> Dict[str, Any]:
    """Format an item for the response"""
    if item_type == "anime":
        # Try multiple column names for rating
        rating = 0.0
        for rating_col in ['Rating', 'rating', 'score', 'Score', 'avg_rating']:
            if rating_col in item.index:
                try:
                    rating_val = item[rating_col]
                    if pd.notna(rating_val) and rating_val != '':
                        rating = float(rating_val)
                        break
                except (ValueError, TypeError):
                    continue
        
        return {
            "id": str(item.get('anime_id', f"anime-{idx}")),
            "title": str(item[col]),
            "image_url": item.get('Image URL'),
            "rating": rating,
            "type": "anime",
            "metadata": {
                "genre": item.get('Genres', ''),
                "year": None,
                "popularity": int(item.get('Popularity', 0)),
                "similarity": 0.8  # Higher similarity for search results
            }
        }
    else:
        # Game data
        rating = _convert_game_rating(item.get('rating', 0))
        return {
            "id": str(item.get('app_id', f"game-{idx}")),
            "title": str(item[col]),
            "image_url": f"https://cdn.akamai.steamstatic.com/steam/apps/{item.get('app_id', '0')}/header.jpg",
            "rating": rating,
            "type": "game",
            "metadata": {
                "genre": "",
                "year": None,
                "popularity": int(item.get('user_reviews', 0)),
                "price": item.get('price_final'),
                "similarity": 0.8  # Higher similarity for search results
            }
        }


def _get_popular_items(item_type: str, limit: int) -> List[Dict[str, Any]]:
    """Get popular items as fallback"""
    try:
        if item_type == "anime" and "popular" in TRAINED_MODELS["anime"]:
            popular_df = TRAINED_MODELS["anime"]["popular"]
            data = TRAINED_MODELS["anime"]["data"]
            
            results = []
            for i, anime_name in enumerate(popular_df[:limit]):
                try:
                    # Find anime by name in the data
                    anime_match = None
                    for col in ['Name', 'name', 'title', 'Title']:
                        if col in data.columns:
                            anime_match = data[data[col] == anime_name]
                            if not anime_match.empty:
                                break
                    
                    if anime_match is not None and not anime_match.empty:
                        anime_info = anime_match.iloc[0]
                        
                        # Get rating
                        rating = 0.0
                        for rating_col in ['Rating', 'rating', 'score', 'Score', 'avg_rating']:
                            if rating_col in anime_info.index:
                                try:
                                    rating_val = anime_info[rating_col]
                                    if pd.notna(rating_val) and rating_val != '':
                                        rating = float(rating_val)
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        results.append({
                            "id": str(anime_info.get('anime_id', f"anime-{i}")),
                            "title": str(anime_name),
                            "image_url": anime_info.get('Image URL'),
                            "rating": rating,
                            "type": "anime",
                            "metadata": {
                                "genre": anime_info.get('Genres', ''),
                                "year": None,
                                "popularity": int(anime_info.get('Popularity', 0)),
                                "similarity": 0.5  # Lower similarity for popular items
                            }
                        })
                except Exception as e:
                    continue
            return results
            
        elif item_type == "game" and "popular" in TRAINED_MODELS["game"]:
            popular_df = TRAINED_MODELS["game"]["popular"]
            data = TRAINED_MODELS["game"]["data"]
            
            results = []
            for i, idx in enumerate(popular_df.head(limit).index):
                try:
                    game_info = data.iloc[idx]
                    
                    title = str(game_info.get('title', 
                                           game_info.get('Title', 
                                           game_info.get('name', 
                                           game_info.get('Name', f"Game {idx}")))))
                    
                    rating = _convert_game_rating(game_info.get('rating', 0))
                    
                    results.append({
                        "id": str(game_info.get('app_id', f"game-{idx}")),
                        "title": title,
                        "image_url": f"https://cdn.akamai.steamstatic.com/steam/apps/{game_info.get('app_id', '0')}/header.jpg",
                        "rating": rating,
                        "type": "game",
                        "metadata": {
                            "genre": "",
                            "year": None,
                            "popularity": int(game_info.get('user_reviews', 0)),
                            "price": game_info.get('price_final'),
                            "similarity": 0.5  # Lower similarity for popular items
                        }
                    })
                except Exception as e:
                    continue
            return results
            
    except Exception as e:
        print(f"Error getting popular items: {e}")
    
    return []


def _coerce_record(obj: Dict[str, Any], item_type: str, idx: int) -> Dict[str, Any] | None:
    # Try common field names
    title = obj.get("title") or obj.get("name") or obj.get("Name") or obj.get("app_name") or obj.get("anime") or obj.get("game") or str(obj.get("Name") or obj.get("Title") or f"Item {idx}")
    image_url = (
        obj.get("image_url") or obj.get("img_url") or obj.get("poster") or obj.get("header_image") or obj.get("thumbnail") or obj.get("Image URL")
    )
    rating = obj.get("rating") or obj.get("score") or obj.get("avg_rating") or obj.get("Rating") or 0.0
    genre = obj.get("genre") or obj.get("genres") or obj.get("tags") or obj.get("Genres") or ""
    year = obj.get("year") or obj.get("release_year") or obj.get("aired") or None
    popularity = obj.get("popularity") or obj.get("pop") or obj.get("rank") or obj.get("Popularity") or obj.get("user_reviews") or 0
    price = obj.get("price") or obj.get("final_price") or obj.get("price_final") or None

    # Sanitize types
    try:
        if item_type == "game":
            rating = _convert_game_rating(rating)
        else:
            rating = float(rating)
    except Exception:
        rating = 0.0
    try:
        year = int(year) if year is not None and str(year).isdigit() else None
    except Exception:
        year = None
    try:
        popularity = int(popularity)
    except Exception:
        popularity = 0

    # Games: infer Steam header if app id present
    app_id = obj.get("app_id") or obj.get("appid") or obj.get("appId")
    if (not image_url or not (isinstance(image_url, str) and image_url.startswith("http"))) and app_id:
        try:
            app_id_str = str(int(app_id))
            image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id_str}/header.jpg"
        except Exception:
            pass

    # Validate title
    title_str = str(title)
    if len(title_str) > 300 or any(k in title_str.lower() for k in ["pandas.core", "numpy.core", "dataframe", "series", "dtype", "ndarray", "index"]):
        return None

    return {
        "id": str(obj.get("id") or obj.get("app_id") or obj.get("anime_id") or f"pop-{idx}"),
        "title": title_str,
        "image_url": image_url if isinstance(image_url, str) and image_url.startswith("http") else None,
        "rating": rating,
        "type": item_type,
        "metadata": {"genre": (", ".join(genre) if isinstance(genre, (list, tuple)) else str(genre or "")), "year": year, "popularity": popularity, "price": price},
    }


def _persist_anime_cache_async():
    def _save():
        try:
            with _anime_img_cache_lock:
                with open(ANIME_IMG_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(ANIME_IMG_CACHE, f, ensure_ascii=False)
        except Exception:
            pass
    t = threading.Thread(target=_save, daemon=True)
    t.start()


def _normalize_anime_title_for_search(t: str) -> str:
    # Remove excessive punctuation and non-letters that can confuse search
    import re
    t = re.sub(r"[\u0000-\u001f]", " ", t)  # control chars
    t = t.replace("☆", " ").replace("★", " ")
    t = re.sub(r"\s+", " ", t).strip()
    # Try to cut after long hyphen/colon segments
    for sep in [" - ", ":", "—", "–", "|", "/"]:
        if sep in t and len(t) > 40:
            t = t.split(sep)[0]
            break
    return t


def _get_anime_image_url(title: str) -> str | None:
    if not title:
        return None
    key = title.strip()
    with _anime_img_cache_lock:
        if key in ANIME_IMG_CACHE:
            return ANIME_IMG_CACHE[key]
    if requests is None:
        return None
    try:
        norm = _normalize_anime_title_for_search(key)
        r = requests.get(
            "https://api.jikan.moe/v4/anime",
            params={"q": norm or key, "limit": 1, "sfw": 1},
            timeout=6,
        )
        if r.ok:
            js = r.json()
            data = (js or {}).get("data") or []
            if data:
                images = data[0].get("images") or {}
                jpg = images.get("jpg") or {}
                url = jpg.get("large_image_url") or jpg.get("image_url") or jpg.get("small_image_url")
                if isinstance(url, str) and url.startswith("http"):
                    with _anime_img_cache_lock:
                        ANIME_IMG_CACHE[key] = url
                    _persist_anime_cache_async()
                    return url
    except Exception:
        return None
    return None


def _convert_game_rating(rating_str: str) -> float:
    """Converts a string rating (e.g., "Very Positive", "Positive", "Mixed") to a numeric rating."""
    if not rating_str:
        return 0.0
    rating_str = rating_str.lower()
    if "very positive" in rating_str:
        return 5.0
    elif "positive" in rating_str:
        return 4.0
    elif "mixed" in rating_str:
        return 3.0
    elif "negative" in rating_str:
        return 2.0
    elif "very negative" in rating_str:
        return 1.0
    else:
        return 0.0


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    CORS(app)

    # Load trained models first
    global TRAINED_MODELS
    TRAINED_MODELS = _load_trained_models()
    
    print("Loaded models:", list(TRAINED_MODELS.keys()))
    for item_type in TRAINED_MODELS:
        print(f"{item_type} models:", list(TRAINED_MODELS[item_type].keys()))
    
    # Load popular items from trained models
    anime_popular = []
    game_popular = []
    
    if "popular" in TRAINED_MODELS["anime"]:
        popular_df = TRAINED_MODELS["anime"]["popular"]
        
        # Handle pandas Index - get the actual data from the full dataset
        if hasattr(popular_df, 'index') and hasattr(popular_df, 'iloc'):
            try:
                # Get the actual anime data from the full dataset
                if "data" in TRAINED_MODELS["anime"]:
                    anime_data = TRAINED_MODELS["anime"]["data"]
                    
                    # Get top 25 popular anime by index
                    for i, idx in enumerate(popular_df.head(25).index):
                        if i >= 25: break
                        try:
                            anime_info = anime_data.iloc[idx]
                            
                            # Try multiple column names for rating
                            rating = 0.0
                            for rating_col in ['Rating', 'rating', 'score', 'Score', 'avg_rating']:
                                if rating_col in anime_info.index:
                                    try:
                                        rating_val = anime_info[rating_col]
                                        if pd.notna(rating_val) and rating_val != '':
                                            rating = float(rating_val)
                                            break
                                    except (ValueError, TypeError):
                                        continue
                            
                            # Try multiple column names for title
                            title = str(anime_info.get('Name', 
                                                   anime_info.get('name', 
                                                   anime_info.get('title', f"Anime {idx}"))))
                            
                            shaped = {
                                "id": str(anime_info.get('anime_id', f"anime-{idx}")),
                                "title": title,
                                "image_url": anime_info.get('Image URL'),
                                "rating": rating,
                                "type": "anime",
                                "metadata": {
                                    "genre": anime_info.get('Genres', ''),
                                    "year": None,
                                    "popularity": int(anime_info.get('Popularity', 0)),
                                }
                            }
                            anime_popular.append(shaped)
                        except Exception as e:
                            print(f"Error processing anime item {idx}: {e}")
                            continue
            except Exception as e:
                print(f"Error processing anime data: {e}")
        elif hasattr(popular_df, 'to_dict'):
            records = popular_df.to_dict(orient='records')
            anime_popular = [_coerce_record(rec, "anime", i) for i, rec in enumerate(records) if _coerce_record(rec, "anime", i)]
        elif hasattr(popular_df, '__iter__'):
            # Handle if it's a pandas Index or other iterable
            try:
                if "data" in TRAINED_MODELS["anime"]:
                    anime_data = TRAINED_MODELS["anime"]["data"]
                    
                    # For Index, we need to find the anime by name in the data
                    for i, anime_name in enumerate(popular_df[:25]):
                        if i >= 25: break
                        try:
                            # Find anime by name in the data
                            anime_match = None
                            for col in ['Name', 'name', 'title', 'Title']:
                                if col in anime_data.columns:
                                    anime_match = anime_data[anime_data[col] == anime_name]
                                    if not anime_match.empty:
                                        break
                            
                            if anime_match is not None and not anime_match.empty:
                                anime_info = anime_match.iloc[0]
                                
                                # Try multiple column names for rating
                                rating = 0.0
                                for rating_col in ['Rating', 'rating', 'score', 'Score', 'avg_rating']:
                                    if rating_col in anime_info.index:
                                        try:
                                            rating_val = anime_info[rating_col]
                                            if pd.notna(rating_val) and rating_val != '':
                                                rating = float(rating_val)
                                                break
                                        except (ValueError, TypeError):
                                            continue
                                
                                shaped = {
                                    "id": str(anime_info.get('anime_id', f"anime-{i}")),
                                    "title": str(anime_name),
                                    "image_url": anime_info.get('Image URL'),
                                    "rating": rating,
                                    "type": "anime",
                                    "metadata": {
                                        "genre": anime_info.get('Genres', ''),
                                        "year": None,
                                        "popularity": int(anime_info.get('Popularity', 0)),
                                    }
                                }
                                anime_popular.append(shaped)
                        except Exception as e:
                            print(f"Error processing anime item {anime_name}: {e}")
                            continue
            except Exception as e:
                print(f"Error processing anime data: {e}")
    
    if "popular" in TRAINED_MODELS["game"]:
        popular_df = TRAINED_MODELS["game"]["popular"]
        
        if hasattr(popular_df, 'index') and hasattr(popular_df, 'iloc'):
            try:
                # Get the actual game data from the full dataset
                if "data" in TRAINED_MODELS["game"]:
                    game_data = TRAINED_MODELS["game"]["data"]
                    
                    # Get top 25 popular games by index
                    for i, idx in enumerate(popular_df.head(25).index):
                        if i >= 25: break
                        try:
                            game_info = game_data.iloc[idx]
                            
                            # Try multiple column names for title
                            title = str(game_info.get('title', 
                                                   game_info.get('Title', 
                                                   game_info.get('name', 
                                                   game_info.get('Name', f"Game {idx}")))))
                            
                            # Convert text rating to numeric
                            rating = _convert_game_rating(game_info.get('rating', 0))
                            
                            shaped = {
                                "id": str(game_info.get('app_id', f"game-{idx}")),
                                "title": title,
                                "image_url": f"https://cdn.akamai.steamstatic.com/steam/apps/{game_info.get('app_id', '0')}/header.jpg",
                                "rating": rating,
                                "type": "game",
                                "metadata": {
                                    "genre": "",
                                    "year": None,
                                    "popularity": int(game_info.get('user_reviews', 0)),
                                    "price": game_info.get('price_final'),
                                }
                            }
                            game_popular.append(shaped)
                        except Exception as e:
                            print(f"Error processing game item {idx}: {e}")
                            continue
            except Exception as e:
                print(f"Error processing game data: {e}")
        elif hasattr(popular_df, 'to_dict'):
            records = popular_df.to_dict(orient='records')
            game_popular = [_coerce_record(rec, "game", i) for i, rec in enumerate(records) if _coerce_record(rec, "game", i)]
        elif hasattr(popular_df, '__iter__'):
            # Handle if it's a list or other iterable
            for i, rec in enumerate(popular_df):
                if isinstance(rec, dict):
                    shaped = _coerce_record(rec, "game", i)
                    if shaped:
                        game_popular.append(shaped)
    
    print(f"Loaded {len(anime_popular)} anime items, {len(game_popular)} game items")
    
    # Get titles for search functionality
    anime_titles = [i.get("title", "") for i in anime_popular]
    game_titles = [i.get("title", "") for i in game_popular]

    @app.route("/")
    def root():
        return send_from_directory(APP_ROOT, "index.html")

    @app.route("/style.css")
    def style():
        return send_from_directory(APP_ROOT, "style.css")

    @app.route("/script.js")
    def script():
        return send_from_directory(APP_ROOT, "script.js")

    @app.route("/api/anime/popular", methods=["GET"])
    def api_anime_popular():
        data = anime_popular[:25]
        # Best-effort image enrichment for anime via Jikan API
        for item in data:
            if not item.get("image_url"):
                url = _get_anime_image_url(item.get("title", ""))
                if url:
                    item["image_url"] = url
        for item in data:
            item.setdefault("type", "anime")
        return jsonify({"success": True, "data": data, "total": len(data)})

    @app.route("/api/games/popular", methods=["GET"])
    def api_games_popular():
        data = game_popular[:25]
        for item in data:
            item.setdefault("type", "game")
        return jsonify({"success": True, "data": data, "total": len(data)})

    @app.route("/api/anime/search/<query>", methods=["GET"])
    def api_anime_search(query: str):
        q = (query or "").strip().lower()
        results = [i for i in anime_popular if q in i.get("title", "").lower()]
        return jsonify({"success": True, "data": results[:50], "total": len(results)})

    @app.route("/api/games/search/<query>", methods=["GET"])
    def api_games_search(query: str):
        q = (query or "").strip().lower()
        results = [i for i in game_popular if q in i.get("title", "").lower()]
        return jsonify({"success": True, "data": results[:50], "total": len(results)})

    @app.route("/api/search-recommendations", methods=["POST"])
    def api_search_recommendations():
        """Search and get top 12 recommendations using trained models"""
        try:
            payload = request.get_json(force=True) or {}
            query = str(payload.get("query", "")).strip()
            item_type = str(payload.get("type", "")).strip().lower()
            limit = int(payload.get("limit", 12))
            
            if not query or item_type not in {"anime", "game"}:
                return jsonify({"success": False, "error": "Invalid payload"}), 400

            # Use trained collaborative filtering models
            shaped = _get_recommendations_from_trained_model(query, item_type, limit)
            
            return jsonify({"success": True, "data": shaped, "total": len(shaped)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/recommend", methods=["POST"])
    def api_recommend():
        try:
            payload = request.get_json(force=True) or {}
            title = str(payload.get("title", "")).strip()
            rec_type = str(payload.get("type", "")).strip().lower()
            limit = int(payload.get("limit", 25))
            limit = 12 if limit == 12 else min(max(limit, 1), 50)
            if not title or rec_type not in {"anime", "game"}:
                return jsonify({"success": False, "error": "Invalid payload"}), 400

            # Use trained collaborative filtering models
            shaped = _get_recommendations_from_trained_model(title, rec_type, limit)
            
            # If no trained recommendations, fallback to fuzzy matching
            if not shaped:
                # Fallback logic here if needed
                shaped = []

            return jsonify({"success": True, "data": shaped, "total": len(shaped)})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)


