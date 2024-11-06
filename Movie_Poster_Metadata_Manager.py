import os
import re
import requests
import winreg
import ctypes
from ctypes import windll, wintypes, POINTER, Structure
import PIL.Image
from bs4 import BeautifulSoup
from urllib.parse import quote
import tkinter as tk
from tkinter import filedialog, ttk
from threading import Thread
import imdb
import subprocess
import csv
from datetime import datetime
import json

ffmpeg_path = r"C:\Users\ericj\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"

class GUID(Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8)
    ]

def clean_filename(filename):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def search_movie(title):
    try:
        # Initialize Cinemagoer
        ia = imdb.Cinemagoer()
        
        # Search for the movie
        movies = ia.search_movie(title)
        
        if movies:
            # Get the first movie result
            movie = ia.get_movie(movies[0].movieID)
            
            # Collect more metadata
            metadata = {
                'title': movie.get('title'),
                'year': movie.get('year'),
                'rating': movie.get('rating'),
                'directors': [d['name'] for d in movie.get('directors', [])],
                'cast': [a['name'] for a in movie.get('cast', [])[:3]],  # First 3 actors
                'genres': movie.get('genres', []),
                'plot': movie.get('plot outline'),
                'runtime': movie.get('runtimes', [''])[0],  # In minutes
                'poster_url': movie['full-size cover url'] if 'full-size cover url' in movie else movie.get('cover url')
            }
            return metadata
                
    except Exception as e:
        print(f"Error searching for movie: {str(e)}")
    
    return None

def save_thumbnail(image_url, file_path, movie_title):
    try:
        if not os.path.exists(file_path):
            print(f"ERROR: Source file not found: {file_path}")
            return False, None
            
        video_dir = os.path.dirname(file_path)
        thumbnails_dir = os.path.join(video_dir, 'thumbnails')
        os.makedirs(thumbnails_dir, exist_ok=True)
        
        # Use IMDb title directly (just clean invalid characters)
        clean_title = clean_filename(movie_title)
        new_video_path = os.path.join(video_dir, f"{clean_title}.mp4")
        
        # Check if paths differ (case-sensitive) even if they're the same when lowercased
        if file_path != new_video_path:
            # Check if target file exists (case-insensitive)
            if os.path.exists(new_video_path) and file_path.lower() != new_video_path.lower():
                print(f"WARNING: Target file already exists, skipping rename: {new_video_path}")
                new_video_path = file_path  # Keep using original file
            else:
                # Make sure source exists before attempting rename
                if os.path.exists(file_path):
                    os.rename(file_path, new_video_path)
                    print(f"Renamed video to: {clean_title}.mp4")
                else:
                    print(f"ERROR: Source file missing before rename: {file_path}")
                    return False, None
        else:
            new_video_path = file_path  # Use existing path
        
        # Verify video file still exists
        if not os.path.exists(new_video_path):
            print(f"ERROR: Video file missing after rename operations: {new_video_path}")
            return False, None
            
        # Use movie title for thumbnail filename
        thumbnail_name = f"{clean_title}.thumb.jpg"
        thumbnail_path = os.path.join(thumbnails_dir, thumbnail_name)
        
        # Download and save the thumbnail
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved thumbnail for: {movie_title}")
            
            # Set the thumbnail using ffmpeg
            if set_video_thumbnail(new_video_path, thumbnail_path):
                return True, new_video_path
            
    except Exception as e:
        print(f"Error saving thumbnail: {str(e)}")
    
    return False, None

def set_video_thumbnail(video_path, thumbnail_path):
    try:
        output_path = video_path + ".temp.mp4"
        
        # Ensure ffmpeg path is correct
        ffmpeg_path = r"C:\Users\ericj\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"  # Update this path
        
        result = subprocess.run([
            ffmpeg_path,
            '-i', video_path,
            '-i', thumbnail_path,
            '-map', '0',
            '-map', '1',
            '-c', 'copy',
            '-disposition:v:1', 'attached_pic',
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            if os.path.exists(output_path):
                if os.path.exists(video_path):
                    os.remove(video_path)
                os.rename(output_path, video_path)
                print(f"Set video thumbnail for: {os.path.basename(video_path)}")
                return True
        else:
            print(f"FFmpeg Error: {result.stderr}")
            if os.path.exists(output_path):
                os.remove(output_path)
            
    except Exception as e:
        print(f"Error setting video thumbnail: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
    
    return False

def set_thumbnail(thumbnail_path, original_file_path):
    try:
        # Windows API constants
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000

        # Refresh Windows shell
        windll.shell32.SHChangeNotify(
            SHCNE_ASSOCCHANGED,
            SHCNF_IDLIST,
            None,
            None
        )

        print(f"Set thumbnail for: {os.path.basename(original_file_path)}")
        
    except Exception as e:
        print(f"Error setting thumbnail: {str(e)}")

def refresh_shell():
    # Refresh Windows shell to update thumbnails
    windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)

def set_video_metadata(video_path, metadata, thumbnail_path):
    try:
        output_path = video_path + ".temp.mp4"
        
        # Build metadata arguments
        metadata_args = []
        if metadata.get('title'):
            metadata_args.extend(['-metadata', f'title={metadata["title"]}'])
        if metadata.get('year'):
            metadata_args.extend(['-metadata', f'date={metadata["year"]}'])
        if metadata.get('plot'):
            metadata_args.extend(['-metadata', f'description={metadata["plot"]}'])
        if metadata.get('genres'):
            metadata_args.extend(['-metadata', f'genre={", ".join(metadata["genres"])}'])
        if metadata.get('directors'):
            metadata_args.extend(['-metadata', f'artist={", ".join(metadata["directors"])}'])
        
        # FFmpeg command with metadata
        result = subprocess.run([
            ffmpeg_path,
            '-i', video_path,
            '-i', thumbnail_path,
            '-map', '0',
            '-map', '1',
            '-c', 'copy',
            '-disposition:v:1', 'attached_pic',
            *metadata_args,  # Add all metadata arguments
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            if os.path.exists(output_path):
                os.replace(video_path, video_path + '.bak')  # Create backup
                os.replace(output_path, video_path)
                os.remove(video_path + '.bak')  # Remove backup after successful operation
                print(f"Set metadata for: {os.path.basename(video_path)}")
                return True
        else:
            print(f"FFmpeg Error: {result.stderr}")
            if os.path.exists(output_path):
                os.remove(output_path)
            
    except Exception as e:
        print(f"Error setting metadata: {str(e)}")
        if os.path.exists(output_path):
            os.remove(output_path)
    
    return False

def get_processed_movies(directory):
    """Read the processed movies log and return sets of both original and new filenames"""
    log_path = os.path.join(directory, 'processed_movies.csv')
    processed_original = set()
    processed_new = set()
    
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed_original.add(row['original_filename'])
                processed_new.add(row['new_filename'])
    
    return processed_original, processed_new

def log_processed_movie(directory, original_filename, metadata):
    """Log processed movie details to CSV"""
    log_path = os.path.join(directory, 'processed_movies.csv')
    file_exists = os.path.exists(log_path)
    
    fieldnames = ['original_filename', 'new_filename', 'processed_date', 'movie_title', 'year', 
                  'directors', 'genres', 'imdb_rating']
    
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'original_filename': original_filename,
            'new_filename': f"{clean_filename(metadata.get('title', ''))}.mp4",
            'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'movie_title': metadata.get('title', ''),
            'year': metadata.get('year', ''),
            'directors': '; '.join(metadata.get('directors', [])),
            'genres': '; '.join(metadata.get('genres', [])),
            'imdb_rating': metadata.get('rating', '')
        })

class MoviePosterScraperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Poster & Metadata Manager")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configure style
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 10))
        
        # Create main frame with padding
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Header
        header = ttk.Label(self.main_frame, text="Movie File Manager", style='Header.TLabel')
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Main tab
        self.main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.main_tab, text="Main")
        
        # Instructions tab
        self.instructions_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.instructions_tab, text="Instructions")
        
        # Add instructions content
        self.create_instructions()
        
        # Directory selection frame (in main tab)
        self.dir_frame = ttk.LabelFrame(self.main_tab, text="Select Directory", padding="10")
        self.dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.dir_entry = ttk.Entry(self.dir_frame)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.dir_frame.columnconfigure(0, weight=1)
        
        self.browse_btn = ttk.Button(self.dir_frame, text="Browse", command=self.browse_directory)
        self.browse_btn.grid(row=0, column=1)
        
        # Add FFmpeg config frame (in main tab)
        self.ffmpeg_frame = ttk.LabelFrame(self.main_tab, text="FFmpeg Configuration", padding="10")
        self.ffmpeg_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        self.ffmpeg_frame.columnconfigure(0, weight=1)

        self.ffmpeg_path_label = ttk.Label(self.ffmpeg_frame, text="Current FFmpeg path: Not set", style='Status.TLabel', wraplength=500)
        self.ffmpeg_path_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.ffmpeg_btn = ttk.Button(self.ffmpeg_frame, text="Set FFmpeg Path", command=self.set_ffmpeg_path)
        self.ffmpeg_btn.grid(row=0, column=1)

        # Status frame (in main tab)
        self.status_frame = ttk.LabelFrame(self.main_tab, text="Processing Status", padding="10")
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_frame.columnconfigure(0, weight=1)
        self.status_frame.rowconfigure(2, weight=1)  # Make status text expandable
        
        # Progress information
        self.progress_label = ttk.Label(self.status_frame, text="Ready", style='Status.TLabel')
        self.progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.status_frame, variable=self.progress_var, maximum=100)
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status text with scrollbar
        self.status_text = tk.Text(self.status_frame, wrap=tk.WORD)
        self.status_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.status_text.config(state=tk.DISABLED)
        
        self.scrollbar = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        self.scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = self.scrollbar.set
        
        # Button frame (in main tab)
        self.button_frame = ttk.Frame(self.main_tab)
        self.button_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.start_btn = ttk.Button(self.button_frame, text="Start Processing", command=self.start_processing)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.test_btn = ttk.Button(self.button_frame, text="Create Test Files", command=self.create_test_files)
        self.test_btn.grid(row=0, column=1, padx=5)
        
        # Configure main tab grid weights
        self.main_tab.columnconfigure(0, weight=1)
        self.main_tab.rowconfigure(2, weight=1)  # Make status frame expandable

        # Configure main frame grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)  # Make notebook expandable
        
        self.processing = False
        
        # Load FFmpeg path on startup
        self.load_ffmpeg_path()

        # Set minimum window size
        self.root.minsize(800, 600)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def log_message(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Force update to ensure scrolling happens immediately
        self.status_text.update_idletasks()
        self.root.update_idletasks()

    def update_progress(self, current, total):
        percentage = (current / total) * 100
        self.progress_var.set(percentage)
        self.progress_label.config(text=f"Processing: {current}/{total} files ({percentage:.1f}%)")
        self.root.update_idletasks()

    def start_processing(self):
        if self.processing:
            return
            
        directory = self.dir_entry.get().strip()
        if not directory:
            self.log_message("⚠️ Please select a directory first.")
            return
        if not os.path.isdir(directory):
            self.log_message("❌ Invalid directory path.")
            return
            
        self.processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Initializing...")
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Start processing in a separate thread
        Thread(target=self.process_directory_thread, args=(directory,), daemon=True).start()

    def process_directory_thread(self, directory):
        try:
            video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.wmv')
            files = [f for f in os.listdir(directory) 
                    if os.path.isfile(os.path.join(directory, f)) 
                    and f.lower().endswith(video_extensions)
                    and not f.startswith('.')]
            total_files = len(files)
            
            processed_original, processed_new = get_processed_movies(directory)
            skipped = 0
            
            self.log_message(f"📁 Found {total_files} video files to process")
            
            for i, filename in enumerate(files, 1):
                if filename in processed_original or filename in processed_new:
                    self.log_message(f"\n⏭️ Skipping already processed file: {filename}")
                    skipped += 1
                    continue
                    
                self.update_progress(i, total_files)
                file_path = os.path.join(directory, filename)
                title = os.path.splitext(filename)[0]
                
                self.log_message(f"\n🎬 Processing: {title}")
                
                metadata = search_movie(title)
                
                if metadata and metadata.get('poster_url'):
                    self.log_message(f"✅ Found poster for: {metadata['title']}")
                    success, new_path = save_thumbnail(metadata['poster_url'], file_path, metadata['title'])
                    if success and new_path:
                        thumbnail_path = os.path.join(os.path.dirname(new_path), 'thumbnails', 
                                                    f"{clean_filename(metadata['title'])}.thumb.jpg")
                        if set_video_metadata(new_path, metadata, thumbnail_path):
                            self.log_message(f"✅ Set metadata for: {os.path.basename(new_path)}")
                            log_processed_movie(directory, filename, metadata)
                        else:
                            self.log_message(f"❌ Failed to set metadata for: {os.path.basename(new_path)}")
                else:
                    self.log_message(f"❌ No poster found for: {title}")
            
            self.log_message(f"\n✨ Processing complete! Skipped {skipped} previously processed files.")
            self.progress_label.config(text="Processing complete!")
            
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
        finally:
            self.processing = False
            self.start_btn.config(state=tk.NORMAL)
            self.test_btn.config(state=tk.NORMAL)

    def create_test_files(self):
        if self.processing:
            return
            
        directory = self.dir_entry.get().strip()
        if not directory:
            self.log_message("⚠️ Please select a directory first.")
            return
        if not os.path.isdir(directory):
            self.log_message("❌ Invalid directory path.")
            return
            
        self.processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.test_btn.config(state=tk.DISABLED)
        
        # Start test file creation in a separate thread
        Thread(target=self.create_test_files_thread, args=(directory,), daemon=True).start()

    def create_test_files_thread(self, output_dir):
        try:
            test_files = [
                "The Shawshank Redemption (1994).mp4",
                "Pulp Fiction (1994).mp4",
                "The Good, the Bad and the Ugly (1966).mp4",
                "12 Angry Men (1957).mp4",
                "Schindler's List (1993).mp4"
            ]
            
            self.log_message("Creating test files...")
            created_files = []
            
            for filename in test_files:
                self.log_message(f"Creating: {filename}")
                filepath = os.path.join(output_dir, filename)
                
                # FFmpeg command to create a valid MP4 file
                result = subprocess.run([
                    ffmpeg_path,
                    '-f', 'lavfi',
                    '-i', f'color=c=black:s=1280x720:d=5',  # 5-second black video
                    '-c:v', 'libx264',
                    '-t', '5',
                    '-pix_fmt', 'yuv420p',
                    filepath
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.log_message(f"Created: {filename}")
                    created_files.append(filepath)
                else:
                    self.log_message(f"Error creating {filename}: {result.stderr}")
            
            self.log_message(f"\nCreated {len(created_files)} test files")
            
        except Exception as e:
            self.log_message(f"Error creating test files: {str(e)}")
        finally:
            self.processing = False
            self.start_btn.config(state=tk.NORMAL)
            self.test_btn.config(state=tk.NORMAL)

    def load_ffmpeg_path(self):
        """Load FFmpeg path from config file"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                global ffmpeg_path
                ffmpeg_path = config.get('ffmpeg_path', '')
                if ffmpeg_path and os.path.exists(ffmpeg_path):
                    self.ffmpeg_path_label.config(text=f"Current FFmpeg path: {ffmpeg_path}")
                else:
                    self.ffmpeg_path_label.config(text="Current FFmpeg path: Not set")
        except FileNotFoundError:
            pass

    def set_ffmpeg_path(self):
        """Open file dialog to select FFmpeg executable"""
        file_path = filedialog.askopenfilename(
            title="Select FFmpeg Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if file_path:
            if os.path.basename(file_path).lower().startswith('ffmpeg'):
                global ffmpeg_path
                ffmpeg_path = file_path
                
                # Save to config file
                config = {'ffmpeg_path': ffmpeg_path}
                with open('config.json', 'w') as f:
                    json.dump(config, f)
                
                self.ffmpeg_path_label.config(text=f"Current FFmpeg path: {ffmpeg_path}")
                self.log_message("✅ FFmpeg path updated successfully")
            else:
                self.log_message("❌ Selected file does not appear to be FFmpeg executable")

    def create_instructions(self):
        """Create the instructions content"""
        # Instructions text
        instructions = """
Movie Poster & Metadata Manager Instructions

1. FFmpeg Setup (Required):
   • Download FFmpeg from: https://ffmpeg.org/download.html
   • Extract the downloaded archive
   • Use the "Set FFmpeg Path" button to select ffmpeg.exe from the bin folder
   • The path should look like: C:\\path\\to\\ffmpeg\\bin\\ffmpeg.exe

2. Basic Usage:
   • Click "Browse" to select a folder containing your movie files
   • Supported formats: MP4, MKV, AVI, MOV, WMV
   • Click "Start Processing" to begin
   • The app will:
     - Search IMDb for each movie
     - Download movie posters
     - Set posters as video thumbnails
     - Add metadata (title, year, directors, etc.)
     - Rename files to match IMDb titles

3. Test Files:
   • Click "Create Test Files" to generate sample movies
   • This creates 5 dummy video files to test the process

4. Notes:
   • Files are processed one at a time
   • Already processed files are skipped
   • A CSV log is created in the movie folder
   • Original files are backed up before modifications

5. Troubleshooting:
   • Ensure FFmpeg path is set correctly
   • Check the status window for error messages
   • Make sure you have internet connection
   • Verify write permissions in the movie folder
"""
        
        # Create scrolled text widget
        text_widget = tk.Text(self.instructions_tab, wrap=tk.WORD, height=20, width=60)
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.instructions_tab, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        text_widget['yscrollcommand'] = scrollbar.set
        
        # Configure grid weights
        self.instructions_tab.columnconfigure(0, weight=1)
        self.instructions_tab.rowconfigure(0, weight=1)
        
        # Insert instructions text
        text_widget.insert('1.0', instructions)
        text_widget.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = MoviePosterScraperUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 