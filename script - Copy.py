import os
import subprocess
import ffmpeg
import re
import datetime

def create_folder(folder_name):
    """Tạo folder nếu chưa tồn tại."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Folder '{folder_name}' created.")
    else:
        print(f"Folder '{folder_name}' already exists.")

def log_processed_file(log_file, old_name, new_name):
    """Ghi lại log file đã được xử lý với tên cũ và mới."""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"{old_name}|{new_name}|{current_time}\n")

def read_processed_files(log_file):
    """Đọc danh sách các file đã xử lý từ log."""
    processed_files = {}
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    old_name = parts[0]
                    new_name = parts[1]
                    time_processed = parts[2] if len(parts) > 2 else ""
                    processed_files[old_name] = {"new_name": new_name, "time": time_processed}
    return processed_files

def sanitize_filename(name):
    """Loại bỏ các ký tự không hợp lệ trong tên tệp để tránh lỗi FFmpeg."""
    # Thay thế các ký tự không hợp lệ bằng dấu gạch dưới
    return re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)

def get_video_resolution_label(file_path):
    """Lấy tên độ phân giải video (FHD, 4K, 2K, HD)."""
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream and 'width' in video_stream and 'height' in video_stream:
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            # 8k
            if width >= 7680 or height >= 4320:
                return "8K"
            # 4k
            elif width >= 3840 or height >= 2160:  # Bao gồm cả 3840x1608
                return "4K"
            # 2k
            elif width >= 2560 or height >= 1440:
                return "2K"
            # FHD
            elif width >= 1920 or height >= 1080:
                return "FHD"
            # HD
            elif width >= 1280 or height >= 720:
                return "HD"
            # 480p
            elif width >= 720 or height >= 480:
                return "480p"
            else:
                return f"{width}p"
    except Exception as e:
        print(f"Error getting resolution for {file_path}: {e}")
    return "unknown_resolution"

def get_movie_year(file_path):
    """Lấy năm của phim từ metadata."""
    try:
        probe = ffmpeg.probe(file_path)
        format_tags = probe.get("format", {}).get("tags", {})
        year = format_tags.get("year", "")
        return year.strip()
    except Exception as e:
        print(f"Error getting year for {file_path}: {e}")
    return ""

def get_language_abbreviation(language_code):
    """Trả về tên viết tắt của ngôn ngữ dựa trên mã ngôn ngữ."""
    language_map = {
        'eng': 'ENG',  # Tiếng Anh
        'vie': 'VIE',  # Tiếng Việt
        'und': 'UNK',  # Không xác định (Undefined)
        'chi': 'CHI',  # Tiếng Trung
        'zho': 'CHI',  # Tiếng Trung (mã khác)
        'jpn': 'JPN',  # Tiếng Nhật
        'kor': 'KOR',  # Tiếng Hàn
        'fra': 'FRA',  # Tiếng Pháp
        'deu': 'DEU',  # Tiếng Đức
        'spa': 'SPA',  # Tiếng Tây Ban Nha
        'ita': 'ITA',  # Tiếng Ý
        'rus': 'RUS',  # Tiếng Nga
        'tha': 'THA',  # Tiếng Thái
        'ind': 'IND',  # Tiếng Indonesia
        'msa': 'MSA',  # Tiếng Malaysia
        'ara': 'ARA',  # Tiếng Ả Rập
        'hin': 'HIN',  # Tiếng Hindi
        'por': 'POR',  # Tiếng Bồ Đào Nha
        'nld': 'NLD',  # Tiếng Hà Lan
        'pol': 'POL',  # Tiếng Ba Lan
        'tur': 'TUR',  # Tiếng Thổ Nhĩ Kỳ
        'swe': 'SWE',  # Tiếng Thụy Điển
        'nor': 'NOR',  # Tiếng Na Uy
        'dan': 'DAN',  # Tiếng Đan Mạch
        'fin': 'FIN',  # Tiếng Phần Lan
        'ukr': 'UKR',  # Tiếng Ukraine
        'ces': 'CES',  # Tiếng Séc
        'hun': 'HUN',  # Tiếng Hungary
        'ron': 'RON',  # Tiếng Romania
        'bul': 'BUL',  # Tiếng Bulgaria
        'hrv': 'HRV',  # Tiếng Croatia
        'srp': 'SRP',  # Tiếng Serbia
        'slv': 'SLV',  # Tiếng Slovenia
        'ell': 'ELL',  # Tiếng Hy Lạp
        'heb': 'HEB',  # Tiếng Do Thái
        'kat': 'KAT',  # Tiếng Georgia
        'lat': 'LAT',  # Tiếng Latin
        'vie-Nom': 'NOM',  # Chữ Nôm
        'cmn': 'CMN',  # Tiếng Trung (Phổ thông)
        'yue': 'YUE',  # Tiếng Quảng Đông
        'nan': 'NAN',  # Tiếng Mân Nam
        'khm': 'KHM',  # Tiếng Khmer
        'lao': 'LAO',  # Tiếng Lào
        'mya': 'MYA',  # Tiếng Miến Điện
        'ben': 'BEN',  # Tiếng Bengal
        'tam': 'TAM',  # Tiếng Tamil
        'tel': 'TEL',  # Tiếng Telugu
        'mal': 'MAL',  # Tiếng Malayalam
        'kan': 'KAN',  # Tiếng Kannada
        'mar': 'MAR',  # Tiếng Marathi
        'pan': 'PAN',  # Tiếng Punjab
        'guj': 'GUJ',  # Tiếng Gujarat
        'ori': 'ORI',  # Tiếng Oriya
        'asm': 'ASM',  # Tiếng Assam
        'urd': 'URD',  # Tiếng Urdu
        'fas': 'FAS',  # Tiếng Ba Tư
        'pus': 'PUS',  # Tiếng Pashto
        'kur': 'KUR',  # Tiếng Kurdish
    }
    return language_map.get(language_code, language_code.upper()[:3])

def rename_simple(file_path):
    """Đổi tên file đơn giản cho trường hợp không có audio để tách."""
    try:
        resolution_label = get_video_resolution_label(file_path)
        probe = ffmpeg.probe(file_path)
        # Lấy ngôn ngữ từ audio stream đầu tiên
        audio_stream = next((stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'audio'), None)
        language = 'und'  # mặc định là undefined
        if audio_stream:
            language = audio_stream.get('tags', {}).get('language', 'und')
        
        language_abbr = get_language_abbreviation(language)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        new_name = f"{resolution_label}_{language_abbr}_{base_name}.mkv"
        new_name = sanitize_filename(new_name)
        
        dir_path = os.path.dirname(file_path)
        new_path = os.path.join(dir_path, new_name)
        
        os.rename(file_path, new_path)
        print(f"Simple renamed file to: {new_name}")
        return new_path
    except Exception as e:
        print(f"Error simple renaming file {file_path}: {e}")
        return file_path

def extract_video_with_audio(file_path, vn_folder, original_folder, log_file):
    """Tách video với audio theo yêu cầu."""
    try:
        probe = ffmpeg.probe(file_path)
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        
        if not audio_streams:
            print(f"No audio found in {file_path}. Performing simple rename.")
            new_path = rename_simple(file_path)
            log_processed_file(log_file, os.path.basename(file_path), os.path.basename(new_path))
            return

        # Lấy thông tin audio đầu tiên để xác định trường hợp
        first_audio = audio_streams[0]
        first_audio_language = first_audio.get('tags', {}).get('language', 'und')

        # Tạo danh sách audio tracks với thông tin cần thiết
        audio_tracks = []
        for stream in audio_streams:
            index = stream.get('index', -1)
            channels = stream.get('channels', 0)
            language = stream.get('tags', {}).get('language', 'und')
            title = stream.get('tags', {}).get('title', get_language_abbreviation(language))
            audio_tracks.append((index, channels, language, title))

        # Sắp xếp theo số kênh giảm dần
        audio_tracks.sort(key=lambda x: x[1], reverse=True)
        
        vietnamese_tracks = [track for track in audio_tracks if track[2] == 'vie']
        non_vietnamese_tracks = [track for track in audio_tracks if track[2] != 'vie']

        if first_audio_language == 'vie':
            # Trường hợp 1: Audio đầu tiên là tiếng Việt
            if non_vietnamese_tracks:
                # Chọn audio không phải tiếng Việt có nhiều kênh nhất
                selected_track = non_vietnamese_tracks[0]
                process_video(file_path, original_folder, selected_track, log_file)
        else:
            # Trường hợp 2: Audio đầu tiên không phải tiếng Việt
            if vietnamese_tracks:
                # Chọn audio tiếng Việt có nhiều kênh nhất
                selected_track = vietnamese_tracks[0]
                process_video(file_path, vn_folder, selected_track, log_file)

    except Exception as e:
        print(f"Exception while processing {file_path}: {e}")

def rename_file(file_path, audio_info, is_output=False):
    """Đổi tên file theo format yêu cầu."""
    try:
        resolution_label = get_video_resolution_label(file_path)
        year = get_movie_year(file_path)
        language = audio_info[2]  # Mã ngôn ngữ
        audio_title = audio_info[3]  # Tiêu đề audio
        
        # Lấy tên gốc của file
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Format chung cho cả file gốc và output:
        # resolution_label + language_abbr + audio_title + year + base_name
        language_abbr = get_language_abbreviation(language)
        new_name = f"{resolution_label}_{language_abbr}_{audio_title}"
        
        if year:
            new_name += f"_{year}"
        new_name += f"_{base_name}.mkv"
        
        new_name = sanitize_filename(new_name)
        
        # Tạo đường dẫn mới
        dir_path = os.path.dirname(file_path)
        new_path = os.path.join(dir_path, new_name)
        
        # Đổi tên file
        os.rename(file_path, new_path)
        print(f"Renamed file to: {new_name}")
        return new_path
    except Exception as e:
        print(f"Error renaming file {file_path}: {e}")
        return file_path

def process_video(file_path, output_folder, selected_track, log_file):
    """Xử lý video với track audio đã chọn và trích xuất subtitle."""
    try:
        # Trích xuất tất cả subtitle
        subtitle_tracks = get_subtitle_info(file_path)
        for sub_track in subtitle_tracks:
            extract_subtitle(file_path, sub_track)
        
        original_filename = os.path.basename(file_path)
        # Đặt tên file đầu ra theo format mới
        resolution_label = get_video_resolution_label(file_path)
        year = get_movie_year(file_path)
        audio_title = selected_track[3]
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file_name = f"{resolution_label}_{audio_title}"
        if year:
            output_file_name += f"_{year}"
        output_file_name += f"_{base_name}.mkv"
        output_file_name = sanitize_filename(output_file_name)
        output_path = os.path.join(output_folder, output_file_name)

        # Sử dụng subprocess để chạy lệnh ffmpeg
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-map', '0:v',
            '-map', f'0:{selected_track[0]}',
            '-c', 'copy',
            '-y',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode == 0 and os.path.exists(output_path):
            print(f"Video saved to {output_path}.")
            
            # Đổi tên file gốc và file output
            probe = ffmpeg.probe(file_path)
            first_audio = next((stream for stream in probe['streams'] 
                              if stream['codec_type'] == 'audio'), None)
            if first_audio:
                first_audio_lang = first_audio.get('tags', {}).get('language', 'und')
                first_audio_title = first_audio.get('tags', {}).get('title', 
                                   get_language_abbreviation(first_audio_lang))
                first_audio_info = (-1, -1, first_audio_lang, first_audio_title)
                
                # Đổi tên file gốc
                new_source_path = rename_file(file_path, first_audio_info)
                new_source_name = os.path.basename(new_source_path)
                
                # Đổi tên file output
                output_original_name = os.path.basename(output_path)
                new_output_path = rename_file(output_path, selected_track, True)
                new_output_name = os.path.basename(new_output_path)
                
                # Ghi log với cả tên cũ và mới
                log_processed_file(log_file, original_filename, new_source_name)
                log_processed_file(log_file, output_original_name, new_output_name)
            return True
        else:
            print(f"Failed to process {file_path}.")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Exception while processing {file_path}: {e}")
        return False

def extract_subtitle(file_path, subtitle_info):
    """Trích xuất subtitle tiếng Việt từ file video."""
    try:
        # Tạo thư mục C:\Subtitles nếu chưa tồn tại
        sub_root_folder = r"C:\Subtitles"
        sub_log_file = os.path.join(sub_root_folder, "subtitles_processed.log")
        create_folder(sub_root_folder)
        
        index, language, title, codec = subtitle_info
        
        # Chỉ xử lý subtitle tiếng Việt
        if language != 'vie':
            # print log cho subtitle không phải tiếng Việt
            print(f"Skipping subtitle for {file_path} as it's not Vietnamese.")
            return False
            
        # Lấy thông tin video để đặt tên
        resolution_label = get_video_resolution_label(file_path)
        year = get_movie_year(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Đặt tên file subtitle với format mới
        sub_filename = f"{resolution_label}_VIE"
        if title:
            sub_filename += f"_{title}"
        if year:
            sub_filename += f"_{year}"
        sub_filename += f"_{base_name}"
        
        # Chọn định dạng đầu ra phù hợp
        output_format = '.srt' if codec in ['subrip', 'srt'] else '.ass'
        sub_filename = sanitize_filename(sub_filename) + output_format
        output_path = os.path.join(sub_root_folder, sub_filename)

        # Kiểm tra xem subtitle đã được xử lý chưa
        processed_subs = read_processed_files(sub_log_file)
        if base_name in processed_subs:
            print(f"Subtitle for {base_name} was already extracted. Skipping.")
            return True

        # Lệnh ffmpeg để trích xuất subtitle
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-map', f'0:{index}',
            '-c', 'copy',
            '-y',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            print(f"Extracted Vietnamese subtitle to: {output_path}")
            log_processed_file(sub_log_file, base_name, sub_filename)
            return True
        else:
            print(f"Failed to extract subtitle: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error extracting subtitle: {e}")
        return False

def get_subtitle_info(file_path):
    """Lấy thông tin về các track subtitle trong file video."""
    try:
        probe = ffmpeg.probe(file_path)
        subtitle_tracks = []
        for stream in probe['streams']:
            if stream['codec_type'] == 'subtitle':
                index = stream.get('index', -1)
                language = stream.get('tags', {}).get('language', 'und')
                title = stream.get('tags', {}).get('title', '')
                codec = stream.get('codec_name', '')
                subtitle_tracks.append((index, language, title, codec))
        return subtitle_tracks
    except Exception as e:
        print(f"Lỗi khi lấy thông tin subtitle từ {file_path}: {e}")
        return []

def main():
    input_folder = "."  # Folder hiện tại
    vn_folder = "Lồng Tiếng - Thuyết Minh"    # Folder cho file tiếng Việt
    original_folder = "Original"  # Folder cho file gốc
    log_file = "processed_files.log"

    # Tạo các folder output nếu chưa tồn tại
    create_folder(vn_folder)
    create_folder(original_folder)

    # Đọc danh sách file đã xử lý
    processed_files = read_processed_files(log_file)

    # Xử lý các file MKV
    try:
        mkv_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".mkv")]
        if not mkv_files:
            print("No MKV files found in the folder.")
            return

        for mkv_file in mkv_files:
            file_path = os.path.join(input_folder, mkv_file)
            print(f"Processing file: {file_path}")

            # Extract subtitle cho tất cả file, kể cả file đã xử lý audio
            subtitle_tracks = get_subtitle_info(file_path)
            if subtitle_tracks:
                for sub_track in subtitle_tracks:
                    extract_subtitle(file_path, sub_track)
            else:
                print(f"No subtitles found in {mkv_file}")

            # Kiểm tra và xử lý audio chỉ cho file chưa xử lý
            if mkv_file in processed_files:
                print(f"File {mkv_file} was processed as {processed_files[mkv_file]['new_name']} on {processed_files[mkv_file]['time']}. Skipping audio processing.")
                continue

            extract_video_with_audio(file_path, vn_folder, original_folder, log_file)

    except Exception as e:
        print(f"Error accessing input folder '{input_folder}': {e}")

if __name__ == "__main__":
    main()