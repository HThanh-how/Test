import os
import subprocess
import ffmpeg
import re
import datetime

def create_folder(folder_name):
    """Tạo folder nếu chưa tồn tại."""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def log_processed_file(log_file, old_name, new_name):
    """Ghi lại log file đã được xử lý với tên cũ và mới."""
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = os.path.join(".", old_name)
    signature = get_file_signature(file_path) if os.path.exists(file_path) else ""
    with open(log_file, "a", encoding='utf-8') as f:
        f.write(f"{old_name}|{new_name}|{current_time}|{signature}\n")

def read_processed_files(log_file):
    """Đọc danh sách các file đã xử lý từ log."""
    processed_files = {}
    processed_signatures = {}
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    old_name = parts[0]
                    new_name = parts[1]
                    time_processed = parts[2] if len(parts) > 2 else ""
                    signature = parts[3] if len(parts) > 3 else ""
                    
                    info = {"new_name": new_name, "time": time_processed, "signature": signature}
                    processed_files[old_name] = info
                    processed_files[new_name] = info
                    if signature:
                        processed_signatures[signature] = info
    return processed_files, processed_signatures

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
        original_filename = os.path.basename(file_path)
        
        # Lấy thông tin cơ bản
        resolution_label = get_video_resolution_label(file_path)
        year = get_movie_year(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Lấy thông tin audio đầu tiên
        probe = ffmpeg.probe(file_path)
        first_audio = next((stream for stream in probe['streams'] 
                          if stream['codec_type'] == 'audio'), None)
        
        if first_audio:
            first_audio_lang = first_audio.get('tags', {}).get('language', 'und')
            first_audio_title = first_audio.get('tags', {}).get('title', 
                               get_language_abbreviation(first_audio_lang))
            
            # Format tên file dựa vào điều kiện
            if first_audio_lang == 'vie':
                # Trường hợp audio đầu tiên là tiếng Việt
                source_name = f"{resolution_label}_{get_language_abbreviation(first_audio_lang)}_{first_audio_title}"
                output_name = f"{resolution_label}_{get_language_abbreviation(selected_track[2])}"
            else:
                # Trường hợp audio đầu tiên không phải tiếng Việt
                source_name = f"{resolution_label}_{get_language_abbreviation(first_audio_lang)}"
                output_name = f"{resolution_label}_{get_language_abbreviation(selected_track[2])}_{selected_track[3]}"
            
            # Thêm năm và tên gốc
            if year:
                source_name += f"_{year}"
                output_name += f"_{year}"
            source_name += f"_{base_name}.mkv"
            output_name += f"_{base_name}.mkv"
            
            # Tạo đường dẫn output
            output_path = os.path.join(output_folder, sanitize_filename(output_name))

            # Xử lý tách audio
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-map', '0:v',
                '-map', f'0:{selected_track[0]}',
                '-c', 'copy',
                '-y',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True)

            if result.returncode == 0 and os.path.exists(output_path):
                print(f"Video saved to {output_path}.")
                
                # Rename file gốc sau khi xử lý thành công
                new_source_path = os.path.join(os.path.dirname(file_path), sanitize_filename(source_name))
                os.rename(file_path, new_source_path)
                print(f"Renamed source file to: {source_name}")
                
                # Ghi log
                log_processed_file(log_file, original_filename, os.path.basename(new_source_path))
                return True
            else:
                print(f"Failed to process {file_path}.")
                if result.stderr:
                    # Decode stderr với error handling
                    stderr_text = result.stderr.decode('utf-8', errors='replace')
                    print(f"Error: {stderr_text}")
                return False
        else:
            print(f"No audio found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Exception while processing {file_path}: {e}")
        return False

def extract_subtitle(file_path, subtitle_info, log_file):
    """Trích xuất subtitle tiếng Việt từ file video."""
    try:
        # Tạo thư mục C:\Subtitles nếu chưa tồn tại
        sub_root_folder = r"C:\Subtitles"
        create_folder(sub_root_folder)
        
        index, language, title, codec = subtitle_info
        
        # Chỉ xử lý subtitle tiếng Việt
        if language != 'vie':
            print(f"Skipping subtitle for {file_path} as it's not Vietnamese.")
            return False
            
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Đặt tên file subtitle giữ nguyên tên gốc
        sub_filename = base_name + '.srt'
        output_path = os.path.join(sub_root_folder, sub_filename)

        # Lệnh ffmpeg để trích xuất subtitle
        cmd = [
            'ffmpeg',
            '-i', file_path,
            '-map', f'0:{index}',
            '-c:s', 'srt',
            '-y',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Extracted Vietnamese subtitle to: {output_path}")
            # Ghi vào log chung
            log_processed_file(log_file, os.path.basename(file_path), sub_filename)
            return True
        else:
            print("Lỗi khi trích xuất subtitle")
            return False
            
    except Exception as e:
        print(f"Lỗi khi trích xuất subtitle: {e}")
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

def get_file_signature(file_path):
    """Lấy chữ ký của file (size và duration) để nhận diện file trùng."""
    try:
        file_size = os.path.getsize(file_path)
        probe = ffmpeg.probe(file_path)
        duration = probe.get('format', {}).get('duration', '0')
        return f"{file_size}_{duration}"
    except Exception as e:
        print(f"Error getting file signature: {e}")
        return None

def main():
    input_folder = "."  # Folder hiện tại
    vn_folder = "Lồng Tiếng - Thuyết Minh"
    original_folder = "Original"
    log_file = os.path.join(r"C:\Subtitles", "processed_files.log")

    create_folder(vn_folder)
    create_folder(original_folder)

    # Đọc danh sách file đã xử lý
    processed_files, processed_signatures = read_processed_files(log_file)

    try:
        mkv_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".mkv")]
        if not mkv_files:
            print("No MKV files found in the folder.")
            return

        for mkv_file in mkv_files:
            file_path = os.path.join(input_folder, mkv_file)
            print(f"Processing file: {file_path}")

            # Kiểm tra file đã xử lý bằng tên và signature
            file_signature = get_file_signature(file_path)
            if mkv_file in processed_files:
                print(f"File {mkv_file} was processed as {processed_files[mkv_file]['new_name']} on {processed_files[mkv_file]['time']}. Skipping.")
                continue
            elif file_signature and file_signature in processed_signatures:
                print(f"File {mkv_file} has same content as processed file {processed_signatures[file_signature]['new_name']}. Skipping.")
                continue

            # Đọc thông tin file một lần duy nhất
            try:
                probe = ffmpeg.probe(file_path)
                audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
                subtitle_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'subtitle']
            except Exception as e:
                print(f"Error probing file {file_path}: {e}")
                continue

            # Kiểm tra subtitle và audio tiếng Việt
            has_vie_subtitle = any(stream.get('tags', {}).get('language', 'und') == 'vie' 
                                 for stream in subtitle_streams)
            has_vie_audio = any(stream.get('tags', {}).get('language', 'und') == 'vie' 
                               for stream in audio_streams)

            # Xử lý subtitle tiếng Việt
            if has_vie_subtitle:
                for stream in subtitle_streams:
                    if stream.get('tags', {}).get('language', 'und') == 'vie':
                        subtitle_info = (
                            stream['index'],
                            'vie',
                            stream.get('tags', {}).get('title', ''),
                            stream.get('codec_name', '')
                        )
                        extract_subtitle(file_path, subtitle_info, log_file)

            # Nếu không có cả subtitle và audio tiếng Việt
            if not has_vie_subtitle and not has_vie_audio:
                print(f"No Vietnamese subtitle and audio found. Renaming file...")
                first_audio = audio_streams[0] if audio_streams else None
                if first_audio:
                    first_audio_lang = first_audio.get('tags', {}).get('language', 'und')
                    first_audio_info = (-1, -1, first_audio_lang, get_language_abbreviation(first_audio_lang))
                    new_path = rename_simple(file_path)
                    log_processed_file(log_file, mkv_file, os.path.basename(new_path))
                continue

            # Xử lý video nếu có audio tiếng Việt
            if has_vie_audio:
                # Tìm audio track tiếng Việt có nhiều kênh nhất
                vie_audio_tracks = [(i, stream.get('channels', 0), 'vie', 
                                   stream.get('tags', {}).get('title', 'VIE'))
                                  for i, stream in enumerate(audio_streams)
                                  if stream.get('tags', {}).get('language', 'und') == 'vie']
                if vie_audio_tracks:
                    # Sắp xếp theo số kênh giảm dần
                    vie_audio_tracks.sort(key=lambda x: x[1], reverse=True)
                    selected_track = vie_audio_tracks[0]
                    extract_video_with_audio(file_path, vn_folder, original_folder, log_file)

    except Exception as e:
        print(f"Error accessing input folder '{input_folder}': {e}")

if __name__ == "__main__":
    main()