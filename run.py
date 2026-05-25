import subprocess
import sys
import os

def check_and_install_dependencies():
    print("====== KHỞI ĐỘNG HỆ THỐNG EV NLP CHATBOT ======")
    print("Kiểm tra các thư viện phụ thuộc...")
    try:
        import fastapi
        import uvicorn
        print("FastAPI và Uvicorn đã được cài đặt.")
    except ImportError:
        print("Đang tiến hành cài đặt thư viện tự động (FastAPI + Uvicorn)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Cài đặt thành công!")
        except Exception as e:
            print(f"Cài đặt thất bại. Vui lòng chạy tay lệnh: pip install -r requirements.txt. Lỗi: {e}")
            sys.exit(1)

if __name__ == "__main__":
    # Đảm bảo đường dẫn làm việc là thư mục chứa script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    check_and_install_dependencies()
    
    print("\nKhởi chạy Uvicorn Server trên Raspberry Pi / Localhost...")
    print("👉 Mở trình duyệt truy cập: http://localhost:8000")
    print("👉 Để dừng server, nhấn Ctrl+C\n")
    
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
