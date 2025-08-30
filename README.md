🎮🎌 MultiDimension - Game and Anime Recommender
A powerful full-stack recommendation system that helps you discover your next favorite anime or game based on intelligent content-based filtering and collaborative recommendations.
🚀 Demo Screenshots
Anime Recommendations
Show Image
Search and discover anime with intelligent recommendations
Game Recommendations
Show Image
Find your next gaming adventure with personalized suggestions
✨ Features

🔍 Smart Search: Real-time search functionality for both anime and games
🎯 Intelligent Recommendations: Content-based filtering using similarity algorithms
📊 Rich Data Display: Beautiful card layouts with ratings, genres, and cover images
🎨 Modern UI: Clean, responsive interface with smooth animations
⚡ Fast Performance: Optimized recommendation engine with caching
🌐 Full-Stack Architecture: Complete web application with API backend

🛠️ Tech Stack
Backend

Python 3.x - Core programming language
Flask - Web framework for API development
Flask-CORS - Cross-origin resource sharing
Pandas - Data manipulation and analysis
NumPy - Numerical computing
Scikit-learn - Machine learning algorithms
Pickle - Model serialization and caching

Frontend

HTML5 - Structure and markup
CSS3 - Modern styling and animations
JavaScript (ES6+) - Interactive functionality
Fetch API - HTTP requests to backend

Data Processing

Matplotlib - Data visualization
Requests - HTTP library for API calls
PIL (Python Imaging Library) - Image processing
Threading - Concurrent operations
JSON - Data serialization

Machine Learning

Content-Based Filtering - Recommendation algorithms
Cosine Similarity - Content similarity calculations
Feature Engineering - Data preprocessing and feature extraction

📁 Project Structure
Current Repository Structure (After Clone)
Game-Anime-Recommender/
├── Anime/
│   └── AnimeR.ipynb          # Anime recommendation model training
├── Game/
│   └── GameR.ipynb          # Game recommendation model training
├── __pycache__/             # Python cache files
├── app.py                   # Flask backend server
├── index.html              # Frontend interface
├── script.js               # Frontend JavaScript
├── style.css               # Styling and animations
└── README.md               # Project documentation
Final Structure (After Training Models)
Game-Anime-Recommender/
├── Anime/
│   ├── AnimeR.ipynb          # Anime recommendation model training
│   ├── anime.awc             # Trained anime cache
│   ├── popular.PC            # Popular anime data
│   ├── pt.pa                 # Anime pivot table
│   └── similarity_scores     # Anime similarity matrix
├── Game/
│   ├── GameR.ipynb          # Game recommendation model training
│   ├── games.gkm             # Trained game cache
│   ├── popular.PG            # Popular games data
│   ├── pt.pg                 # Game pivot table
│   └── similarity_scores     # Game similarity matrix
├── __pycache__/             # Python cache files
├── app.py                   # Flask backend server
├── index.html              # Frontend interface
├── script.js               # Frontend JavaScript
├── style.css               # Styling and animations
└── README.md               # Project documentation
🚀 Quick Start
Prerequisites
Make sure you have Python 3.x installed on your system.
Installation

Clone the repository
bashgit clone https://github.com/your-username/Game-Anime-Recommender.git
cd Game-Anime-Recommender

Install required packages
bashpip install flask flask-cors pandas numpy scikit-learn matplotlib requests pillow

Download and prepare datasets
Anime Dataset: [https://www.kaggle.com/datasets/dbdmobile/myanimelist-dataset]
Game Dataset: [https://www.kaggle.com/datasets/antonkozyriev/game-recommendations-on-steam]

🔧 Setup Instructions
⚠️ Important: The trained model files are not included in this repository due to their massive size (15+ GB combined). GitHub has file size limitations, and uploading such large files would make the repository impractical to clone and use. You need to generate these files locally by running the training notebooks:

Generate Anime Models

Open Anime/AnimeR.ipynb in Jupyter Notebook
Run all cells to train the anime recommendation model
This will generate the following files in the Anime/ directory:

anime.awc - Anime cache file
popular.PC - Popular anime data
pt.pa - Anime pivot table
similarity_scores - Anime similarity matrix




Generate Game Models

Open Game/GameR.ipynb in Jupyter Notebook
Run all cells to train the game recommendation model
This will generate the following files in the Game/ directory:

games.gkm - Game cache file
popular.PG - Popular games data
pt.pg - Game pivot table
similarity_scores - Game similarity matrix




Verify File Structure

Ensure your folder structure matches the "Final Structure" shown above
All generated files must be in their respective Anime/ and Game/ directories
The Flask app (app.py) expects these files to be in these exact locations


Start the application
bash# Start the Flask backend server
python app.py

# Open index.html in your web browser
# The app runs on http://localhost:5000


🚨 Troubleshooting: If you get file not found errors, make sure you've completed steps 1-3 above. The application cannot run without the trained model files being generated first.
🎯 How It Works
Recommendation Algorithm
The system uses content-based filtering with the following approach:

Feature Engineering: Extract meaningful features from anime/game metadata (genres, ratings, descriptions, etc.)
Similarity Calculation: Use cosine similarity to find content relationships
Recommendation Generation: Suggest items based on user preferences and content similarity
Caching System: Store trained models using pickle for fast retrieval

API Endpoints

/api/anime/search - Search anime database
/api/game/search - Search game database
/api/anime/recommend - Get anime recommendations
/api/game/recommend - Get game recommendations
/api/popular/anime - Fetch popular anime
/api/popular/games - Fetch popular games

🎨 Features in Detail
Search Functionality

Real-time search as you type
Fuzzy matching for better results
Category filtering (genres, ratings, etc.)

Recommendation Engine

Content-based filtering using multiple features
Similarity scoring with weighted algorithms
Personalized suggestions based on user interaction

User Interface

Responsive grid layout for content cards
Smooth animations and transitions
Modal dialogs for detailed information
Tab-based navigation between anime and games

🔧 Configuration
The application uses several configuration files:

Flask Server: Runs on localhost:5000 by default
CORS: Enabled for cross-origin requests
Cache Settings: Optimized for performance
Image Loading: Dynamic loading from external APIs

📊 Datasets
This project uses comprehensive datasets containing:
Anime Dataset

Anime titles, genres, ratings, episodes
User ratings and reviews
Studio information, air dates
Synopsis and metadata

Game Dataset

Game titles, platforms, genres
User ratings and reviews
Release dates, publishers
Screenshots and metadata

Dataset links will be provided separately due to size constraints
🤝 Contributing

Fork the repository
Create a feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

🙏 Acknowledgments

Thanks to the anime and gaming communities for providing rich datasets
Special appreciation to open-source libraries that made this project possible
Inspired by recommendation systems from major platforms

📧 Contact
Aaditya Nepal - @your-handle
Project Link: https://github.com/Aaditya-Nepal/Game-Anime-Recommender

⭐ Found this helpful? Give it a star! ⭐
