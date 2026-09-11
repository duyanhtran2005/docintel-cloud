import os
import sys
import logging

# Set PYTHONPATH để có thể import từ folder src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from services.storage import MinioStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("🚀 TEST MINIO STORAGE LAYER VỚI FILE PDF THẬT")
    print("=" * 60)

    # 1. Khởi tạo MinioStorage
    storage = MinioStorage()
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "documents")

    # 2. Xử lý đường dẫn file từ tham số truyền vào (hoặc mặc định)
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Nếu người dùng không truyền tham số, tìm file PDF bất kỳ trong thư mục hiện tại
        pdf_files = [f for f in os.listdir(".") if f.lower().endswith(".pdf")]
        if pdf_files:
            pdf_path = pdf_files[0]
            logger.info(f"Phát hiện file PDF trong thư mục: '{pdf_path}'")
        else:
            print("⚠️ Chưa truyền đường dẫn file PDF!")
            print("💡 Cú pháp: python test_upload.py <đường_dẫn_file_pdf>")
            print("   Ví dụ: python test_upload.py C:/Users/Downloads/my_doc.pdf")
            print("   Hoặc copy 1 file PDF vào thư mục docintel-cloud rồi chạy: python test_upload.py ten_file.pdf")
            return

    if not os.path.exists(pdf_path):
        logger.error(f"File PDF không tồn tại tại đường dẫn: '{pdf_path}'")
        return

    filename = os.path.basename(pdf_path)
    object_name = f"pdfs/{filename}"

    # 3. Tiến hành Upload PDF lên MinIO
    logger.info(f"Đang upload file PDF '{pdf_path}' lên bucket '{bucket_name}' với key '{object_name}'...")
    success = storage.upload_file(bucket_name, pdf_path, object_name)

    if success:
        print(f"\n✅ UPLOAD FILE PDF '{filename}' THÀNH CÔNG!")
        
        # 4. Kiểm tra đọc Stream từ MinIO
        logger.info(f"Đang kiểm tra đọc lại stream của object '{object_name}'...")
        stream = storage.get_file_stream(bucket_name, object_name)
        file_bytes = stream.read()
        print(f"📊 Đã tải stream thành công! Kích thước file PDF trên MinIO: {len(file_bytes):,} bytes ({len(file_bytes)/1024:.2f} KB)")
        print("🎉 TEST UPLOAD FILE PDF HOÀN TẢO!")
    else:
        print("❌ UPLOAD FILE PDF THẤT BẠI. Vui lòng kiểm tra lại MinIO container!")

if __name__ == "__main__":
    main()
