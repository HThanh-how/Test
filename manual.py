import os
import subprocess
import ffmpeg
import re
import datetime
from tkinter import filedialog
import tkinter as tk

def create_folder(folder_name):
    """Tạo folder nếu chưa tồn tại."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def sanitize_filename(name):
    """Loại bỏ các ký tự không hợp lệ trong tên tệp."""
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)

def get_video_resolution_label(file_path):
    """Lấy tên độ phân giải video."""
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream and 'width' in video_stream and 'height' in video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            if width >= 7680 or height >= 4320:
                return "8K"
            elif width >= 3840 or height >= 2160:
                return "4K"
            elif width >= 2560 or height >= 1440:
                return "2K"
            elif width >= 1920 or height >= 1080:
                return "FHD"
            elif width >= 1280 or height >= 720:
                return "HD"
            elif width >= 720 or height >= 480:
                return "480p"
            else:
                return f"{width}p"
    except Exception as e:
        print(f"Error getting resolution: {e}")
    return "unknown_resolution"

def get_movie_year(file_path):
    """Lấy năm của phim từ metadata."""
    try:
        probe = ffmpeg.probe(file_path)
        format_tags = probe.get("format", {}).get("tags", {})
        year = format_tags.get("year", "")
        return year.strip()
    except Exception as e:
        print(f"Error getting year: {e}")
    return ""

def get_language_abbreviation(language_code):
    """Trả về tên viết tắt của ngôn ngữ."""
    language_map = {
        'eng': 'ENG', 'vie': 'VIE', 'und': 'UNK',
        'chi': 'CHI', 'jpn': 'JPN', 'kor': 'KOR',
        'fra': 'FRA', 'deu': 'DEU', 'spa': 'SPA'
    }
    return language_map.get(language_code, language_code.upper()[:3])

def process_single_file(file_path):
    """Xử lý một file được chọn."""
    try:
        # Tạo folders
        vn_folder = "Lồng Tiếng - Thuyết Minh"
        original_folder = "Original"
        sub_folder = r"C:\Subtitles"
        log_file = os.path.join(sub_folder, "processed_files.log")
        
        create_folder(vn_folder)
        create_folder(original_folder)
        create_folder(sub_folder)
        
        # Lấy thông tin audio
        probe = ffmpeg.probe(file_path)
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
        
        if not audio_streams:
            print("Không tìm thấy audio stream nào.")
            return
            
        # Hiển thị thông tin audio streams
        print("\nDanh sách Audio Streams:")
        for i, stream in enumerate(audio_streams):
            lang = stream.get('tags', {}).get('language', 'und')
            title = stream.get('tags', {}).get('title', get_language_abbreviation(lang))
            channels = stream.get('channels', 0)
            print(f"{i+1}. Language: {lang}, Title: {title}, Channels: {channels}")
            
        # Hiển thị thông tin subtitle streams
        if subtitle_streams:
            print("\nDanh sách Subtitle Streams:")
            for i, stream in enumerate(subtitle_streams):
                lang = stream.get('tags', {}).get('language', 'und')
                title = stream.get('tags', {}).get('title', '')
                print(f"{i+1}. Language: {lang}, Title: {title}")
        
        # Cho người dùng chọn
        while True:
            choice = input("\nBạn muốn làm gì?\n1. Tách audio\n2. Trích xuất subtitle\n3. Thoát\nChọn: ")
            
            if choice == '1':
                audio_choice = int(input("Chọn số thứ tự audio stream (0 để bỏ qua): "))
                if 0 < audio_choice <= len(audio_streams):
                    selected_audio = audio_streams[audio_choice-1]
                    process_audio(file_path, selected_audio, vn_folder, original_folder, log_file)
                    
            elif choice == '2':
                sub_choice = int(input("Chọn số thứ tự subtitle stream (0 để bỏ qua): "))
                if 0 < sub_choice <= len(subtitle_streams):
                    selected_sub = subtitle_streams[sub_choice-1]
                    extract_subtitle(file_path, selected_sub, log_file)
                    
            elif choice == '3':
                break
                
    except Exception as e:
        print(f"Lỗi khi xử lý file: {e}")

def process_audio(file_path, selected_audio, vn_folder, original_folder, log_file):
    """Xử lý audio được chọn."""
    try:
        resolution_label = get_video_resolution_label(file_path)
        year = get_movie_year(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Xác định ngôn ngữ và thư mục đích
        audio_lang = selected_audio.get('tags', {}).get('language', 'und')
        audio_title = selected_audio.get('tags', {}).get('title', 
                     get_language_abbreviation(audio_lang))
        
        output_folder = vn_folder if audio_lang == 'vie' else original_folder
        output_name = f"{resolution_label}_{get_language_abbreviation(audio_lang)}_{audio_title}"
        if year:
            output_name += f"_{year}"
        output_name += f"_{base_name}.mkv"
        output_path = os.path.join(output_folder, sanitize_filename(output_name))
        
        # Tách audio
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-map', '0:v',
            '-map', f'0:{selected_audio["index"]}',
            '-c', 'copy',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Đã tách thành công: {output_path}")
            # Ghi log khi xử lý thành công
            log_processed_file(log_file, os.path.basename(file_path), os.path.basename(output_path))
        else:
            print("Lỗi khi tách audio")
            
    except Exception as e:
        print(f"Lỗi khi xử lý audio: {e}")

def extract_subtitle(file_path, subtitle_stream, log_file):
    """Trích xuất subtitle được chọn."""
    try:
        sub_folder = r"C:\Subtitles"
        create_folder(sub_folder)
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        lang = subtitle_stream.get('tags', {}).get('language', 'und')
        title = subtitle_stream.get('tags', {}).get('title', '')
        
        sub_name = f"{base_name}_{get_language_abbreviation(lang)}"
        if title:
            sub_name += f"_{title}"
        sub_name = sanitize_filename(sub_name) + '.srt'
        
        output_path = os.path.join(sub_folder, sub_name)
        
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-map', f'0:{subtitle_stream["index"]}',
            '-c:s', 'srt',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Đã trích xuất subtitle: {output_path}")
            # Ghi log khi trích xuất thành công
            log_processed_file(log_file, os.path.basename(file_path), sub_name)
        else:
            print("Lỗi khi trích xuất subtitle")
            
    except Exception as e:
        print(f"Lỗi khi trích xuất subtitle: {e}")

def read_log_file():
    """Đọc và hiển thị nội dung file log."""
    try:
        log_file = os.path.join(r"C:\Subtitles", "processed_files.log")
        if os.path.exists(log_file):
            print("\n=== NỘI DUNG FILE LOG ===")
            with open(log_file, "r", encoding='utf-8') as f:
                for line in f:
                    old_name, new_name, time = line.strip().split('|')
                    print(f"Thời gian: {time}")
                    print(f"File gốc: {old_name}")
                    print(f"File mới: {new_name}")
                    print("-" * 50)
        else:
            print("\nChưa có file log.")
    except Exception as e:
        print(f"Lỗi khi đọc file log: {e}")

def main():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính
    
    while True:
        print("\n=== CHƯƠNG TRÌNH XỬ LÝ VIDEO ===")
        print("1. Chọn file để xử lý")
        print("2. Xem log file")
        print("3. Thoát")
        
        choice = input("Lựa chọn của bạn: ")
        
        if choice == '1':
            file_path = filedialog.askopenfilename(
                title="Chọn file video",
                filetypes=[("MKV files", "*.mkv")]
            )
            if file_path:
                process_single_file(file_path)
        elif choice == '2':
            read_log_file()
        elif choice == '3':
            break
        else:
            print("Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main() 