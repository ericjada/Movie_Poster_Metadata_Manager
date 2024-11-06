# Movie Poster & Metadata Manager

A Python application that automatically processes movie files by fetching metadata from IMDb, downloading movie posters, and setting them as video thumbnails.

## Features

- 🎬 Fetches movie metadata from IMDb
- 🖼️ Downloads and sets movie posters as video thumbnails
- 📝 Renames files to match IMDb titles
- 📊 Logs processing history in CSV format
- ⚡ Multi-threaded processing
- 🧪 Test file generation for demo purposes

## Prerequisites

- Python 3.8+
- FFmpeg installed on your system
- Windows OS (for thumbnail functionality)

### Required Python Packages

```bash
pip install requests pillow beautifulsoup4 cinemagoer urllib3
```

Or install all dependencies using requirements.txt:
```bash
pip install -r requirements.txt
```

Note: Some packages like `tkinter` and `ctypes` come with Python's standard library.

You should also create a requirements.txt file containing:
```
requests
pillow
beautifulsoup4
cinemagoer
urllib3
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/movie-poster-manager.git
cd movie-poster-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download FFmpeg:
   - Visit [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Download the Windows build
   - Extract the archive
   - Note the path to `ffmpeg.exe` in the `bin` folder

## Usage

1. Run the application:
```bash
python movie_poster_scraper.py
```

2. In the application:
   - Set the FFmpeg path using the "Set FFmpeg Path" button
   - Click "Browse" to select a folder containing movie files
   - Click "Create Test Files" to generate sample movies (optional)
   - Click "Start Processing" to begin metadata fetching

### Supported File Formats

- MP4 (.mp4)
- MKV (.mkv)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)

### Processing Steps

1. Scans selected directory for video files
2. Extracts movie title from filename
3. Searches IMDb for movie metadata
4. Downloads movie poster
5. Sets poster as video thumbnail
6. Renames file to match IMDb title
7. Logs processing details to CSV

## File Structure

```
movie-poster-manager/
├── Movie_Poster_Metadata_Manager.py  # Main application
├── create_test_files.py              # Test file generator
├── config.json                       # FFmpeg path configuration
├── requirements.txt                  # Python dependencies
└── README.md                         # Documentation
```

## Generated Files

The application creates:

- `thumbnails/` directory in the processed folder containing:
  - Movie poster images (.jpg)
  - Named according to movie titles
- `processed_movies.csv` log file containing:
  - Original filename
  - New filename
  - Processing date
  - Movie title
  - Year
  - Directors (semicolon separated)
  - Genres (semicolon separated)
  - IMDb rating
- `config.json` storing FFmpeg path configuration

## Error Handling

- Validates FFmpeg installation
- Skips previously processed files
- Logs errors in the status window
- Maintains original files until processing succeeds

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- IMDb data provided by IMDbPY
- FFmpeg for video processing
- Movie data from IMDb (www.imdb.com)

## Screenshots

*(Add screenshots of your application here)*

## Known Issues

- Thumbnail functionality is Windows-specific
- Some movie titles may not be correctly parsed from filenames
- FFmpeg path must be set manually on first run
- Movie title matching depends on filename accuracy
- Large files may take longer to process
- Some IMDb metadata might be incomplete

## Future Improvements

- [ ] Cross-platform thumbnail support
- [ ] Batch processing optimization
- [ ] Additional metadata sources
- [ ] Custom naming templates
- [ ] Video format conversion options

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
