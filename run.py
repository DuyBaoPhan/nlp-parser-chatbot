import os
import subprocess
import sys


def check_and_install_dependencies():
    print("====== KHỞI ĐỘNG HỆ THỐNG EV NLP CHATBOT ======")
    print("Kiểm tra các thư viện phụ thuộc...")
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401

        print("FastAPI và Uvicorn đã được cài đặt.")
    except ImportError:
        print("Đang cài đặt thư viện tự động từ requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Cài đặt thành công.")
        except Exception as exc:
            print(f"Cài đặt thất bại. Hãy chạy thủ công: pip install -r requirements.txt. Lỗi: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)

    check_and_install_dependencies()

    print("\nKhởi chạy Uvicorn Server...")
    print("Mở trình duyệt truy cập: http://localhost:8000")
    print("Để dừng server, nhấn Ctrl+C\n")

    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
