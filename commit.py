import os
import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    filename='auto_commit.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def find_git_repo():
    """Tìm thư mục Git repository gần nhất."""
    current = os.getcwd()
    while current != os.path.dirname(current):  # Dừng khi lên tới thư mục gốc
        if os.path.exists(os.path.join(current, '.git')):
            return current
        current = os.path.dirname(current)
    return None

def is_large_file(file_path, max_size_mb=100):
    """Kiểm tra xem file có lớn hơn giới hạn không."""
    try:
        if not os.path.exists(file_path):
            return False
        max_size_bytes = max_size_mb * 1024 * 1024
        return os.path.getsize(file_path) > max_size_bytes
    except Exception as e:
        logging.error(f"Lỗi kiểm tra kích thước file {file_path}: {e}")
        return True

def auto_git_commit():
    """Tự động commit và push code lên GitHub."""
    try:
        # Tìm và chuyển đến thư mục Git repository
        git_repo = find_git_repo()
        if not git_repo:
            print("Không tìm thấy Git repository trong các thư mục cha.")
            return False
        
        os.chdir(git_repo)
        print(f"Đang làm việc trong repository: {git_repo}")

        # Kiểm tra trạng thái git
        status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if 'nothing to commit' in status.stdout:
            print("Không có thay đổi để commit")
            return False

        # Lấy danh sách file thay đổi
        changed_files = subprocess.run(['git', 'diff', '--name-only'], 
                                     capture_output=True, text=True).stdout.splitlines()
        
        # Thêm các file chưa được track
        untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'],
                                 capture_output=True, text=True).stdout.splitlines()
        changed_files.extend(untracked)

        # Kiểm tra và bỏ qua các file lớn
        for file in changed_files:
            try:
                if not os.path.exists(file):
                    print(f"Bỏ qua file không tồn tại: {file}")
                    continue
                if is_large_file(file):
                    print(f"Bỏ qua file lớn: {file}")
                    subprocess.run(['git', 'reset', file], capture_output=True)
            except Exception as e:
                print(f"Lỗi xử lý file {file}: {e}")
                continue

        # Add các file còn lại
        subprocess.run(['git', 'add', '.'])
        
        # Kiểm tra lại xem còn gì để commit không
        status = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if 'nothing to commit' in status.stdout:
            print("Không có file phù hợp để commit")
            return False
        
        # Commit và push
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Auto commit at {current_time}"
        
        subprocess.run(['git', 'commit', '-m', commit_message])
        subprocess.run(['git', 'push'])
        
        print(f"Đã commit và push thành công lúc: {current_time}")
        logging.info("Đã commit và push thành công")
        return True
        
    except Exception as e:
        error_msg = f"Lỗi khi commit code: {e}"
        print(error_msg)
        logging.error(error_msg)
        return False

if __name__ == "__main__":
    auto_git_commit() 