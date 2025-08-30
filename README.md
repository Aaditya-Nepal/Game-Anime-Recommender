# MultiDimension - Anime & Game Recommender

A full-stack recommendation system that helps you discover anime and games using content-based filtering and machine learning algorithms.

## Features

- **Smart Search**: Real-time search with fuzzy matching for both anime and games
- **Content-Based Recommendations**: Uses similarity algorithms to suggest relevant content
- **Modern Interface**: Clean, responsive design with smooth animations
- **Fast Performance**: Optimized recommendation engine with model caching
- **Rich Data Display**: Detailed cards showing ratings, genres, and descriptions

## Tech Stack

**Backend**
- Python 3.x with Flask web framework
- Flask-CORS for cross-origin requests
- Pandas and NumPy for data processing
- Scikit-learn for machine learning algorithms
- Pickle for model serialization

**Frontend**
- HTML5, CSS3, and modern JavaScript
- Fetch API for backend communication
- Responsive design for all devices

**Machine Learning**
- Content-based filtering using cosine similarity
- Feature engineering for better recommendations
- Cached similarity matrices for performance

## Project Structure

```
MultiDimension/
├── Anime/
│   ├── AnimeR.ipynb          # Anime model training
│   ├── anime.awc             # Anime cache (generated)
│   ├── popular.PC            # Popular anime data (generated)
│   ├── pt.pa                 # Pivot table (generated)
│   └── similarity_scores     # Similarity matrix (generated)
├── Game/
│   ├── GameR.ipynb           # Game model training
│   ├── games.gkm             # Game cache (generated)
│   ├── popular.PG            # Popular games data (generated)
│   ├── pt.pg                 # Pivot table (generated)
│   └── similarity_scores     # Similarity matrix (generated)
├── app.py                    # Flask backend
├── index.html               # Frontend interface
├── script.js                # JavaScript functionality
├── style.css                # Styling
└── README.md                # Documentation
```

## Installation

### Prerequisites
- Python 3.x installed on your system

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/MultiDimension.git
   cd MultiDimension
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-cors pandas numpy scikit-learn matplotlib requests pillow
   ```

3. **Download datasets**
   - [Anime Dataset](https://www.kaggle.com/datasets/dbdmobile/myanimelist-dataset)
   - [Game Dataset](https://www.kaggle.com/datasets/antonkozyriev/game-recommendations-on-steam)

## Model Training

> **Important**: Model files are not included due to size constraints (15+ GB). You must generate them locally.

### Train Anime Model
1. Open `Anime/AnimeR.ipynb` in Jupyter Notebook
2. Run all cells to generate required files in the Anime directory

### Train Game Model
1. Open `Game/GameR.ipynb` in Jupyter Notebook
2. Run all cells to generate required files in the Game directory

### Start the Application
```bash
python app.py
```

The server will start at `http://localhost:5000`

## How It Works

The recommendation system uses content-based filtering:

1. **Feature Engineering**: Extracts features from anime/game metadata (genres, ratings, descriptions)
2. **Similarity Calculation**: Uses cosine similarity to find content relationships
3. **Recommendation Generation**: Suggests items based on content similarity
4. **Caching**: Stores trained models using pickle for fast retrieval

## API Endpoints

- `GET /api/anime/search` - Search anime database
- `GET /api/game/search` - Search game database
- `POST /api/anime/recommend` - Get anime recommendations
- `POST /api/game/recommend` - Get game recommendations
- `GET /api/popular/anime` - Get popular anime
- `GET /api/popular/games` - Get popular games

## Configuration

- **Server**: Runs on localhost:5000 by default
- **CORS**: Enabled for cross-origin requests
- **Cache**: Optimized for performance with pickle serialization

## Data Sources

**Anime Dataset**
- Comprehensive anime metadata including titles, genres, ratings
- User ratings and reviews
- Studio information and air dates

**Game Dataset**
- Game titles, platforms, and genres
- User ratings and community reviews
- Release information and metadata

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## Troubleshooting

- **File not found errors**: Ensure you've completed model training steps
- **Import errors**: Check that all dependencies are installed
- **Server issues**: Verify Flask is running on the correct port

## Contact

**Author**: Aaditya Nepal  
**Repository**: [Game&AnimeR](https://github.com/Aaditya-Nepal/Game-Anime-Recommender)
