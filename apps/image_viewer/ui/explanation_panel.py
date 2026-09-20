from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget


class ExplanationPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.text = QTextEdit()
        self.text.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text)

    def update_for_operation(self, operation: str, params: dict, metadata: dict | None = None) -> None:
        metadata = metadata or {}
        if operation == "Zoom":
            html = f"""
            <h3>Thuật toán: Phóng to / Thu nhỏ ảnh (Image Scaling)</h3>
            <p><b>Tham số hiện tại:</b><br>
            • Tỉ lệ thu phóng (Scale): {params.get("scale", 1.0):.2f}x<br>
            • Phương pháp nội suy (Interpolation): {params.get("interpolation", "Bilinear")}</p>
            
            <p><b>Khái niệm:</b><br>
            Thu phóng thay đổi kích thước ảnh bằng cách tái lấy mẫu (resampling) các điểm ảnh (pixel) trên một lưới tọa độ lớn hơn hoặc nhỏ hơn.</p>
            
            <p><b>Các phương pháp nội suy:</b><br>
            • <b>Nearest Neighbor (Láng giềng gần nhất):</b> Tốc độ nhanh nhất, gán giá trị của pixel gần nhất; dễ làm ảnh bị răng cưa (pixelated).<br>
            • <b>Bilinear (Nội suy song tuyến tính):</b> Tính trung bình có trọng số từ 4 pixel lân cận, giúp ảnh mịn màng, cân bằng tốt giữa chất lượng và tốc độ.<br>
            • <b>Bicubic (Nội suy bậc ba):</b> Sử dụng vùng lân cận 16 pixel (4x4), làm mịn rất tốt, thích hợp khi phóng to chất lượng cao nhưng tốn tài nguyên tính toán hơn.</p>
            
            <p><b>Nguyên lý tính toán:</b><br>
            Với mỗi pixel ở ảnh đầu ra (x', y'), thuật toán ánh xạ ngược về tọa độ thực (x, y) trên ảnh gốc và nội suy giá trị màu tương ứng.</p>
            
            <p><b>Đánh giá kết quả:</b><br>
            Phóng to quá lớn có thể làm lộ nhược điểm nội suy (mờ hoặc vỡ nét). Thu nhỏ quá nhiều có thể làm mất các chi tiết nhỏ.</p>
            """
        elif operation == "Rotate":
            matrix = metadata.get("matrix")
            matrix_text = ""
            if isinstance(matrix, np.ndarray):
                matrix_text = "<pre style='background:#202637; padding:8px; border-radius:6px; font-weight:bold;'>" + "\n".join("  ".join(f"{value:8.3f}" for value in row) for row in matrix) + "</pre>"
            clipping_note = "Có (4 góc bị tràn ra ngoài kích thước khung ban đầu)" if metadata.get("clipping_occurs") else "Không bị cắt góc"
            html = f"""
            <h3>Thuật toán: Phép xoay Affine (Affine Rotation)</h3>
            <p><b>Tham số hiện tại:</b><br>
            • Góc xoay (Angle): {params.get("angle", 0):.0f}°<br>
            • Phương pháp nội suy (Interpolation): {params.get("interpolation", "Bilinear")}<br>
            • Chế độ bù viền (Border mode): {params.get("border_mode", "Constant Black")}</p>
            
            <p><b>Khái niệm:</b><br>
            Xoay ảnh quanh tâm bằng phép biến đổi hình học Affine (bảo toàn tính đồng phẳng và tỉ lệ đoạn thẳng song song).</p>
            
            <p><b>Triển khai trong OpenCV:</b><br>
            • Sử dụng hàm <code>cv2.getRotationMatrix2D(center, angle, scale)</code> để tính ma trận biến đổi 2x3.<br>
            • Sử dụng hàm <code>cv2.warpAffine(...)</code> để thực hiện ánh xạ tọa độ và tái lấy mẫu các pixel.</p>
            
            <p><b>Ma trận xoay Affine 2x3:</b>{matrix_text}</p>
            
            <p><b>Ý nghĩa ma trận:</b><br>
            Ma trận chứa các thành phần lượng giác cos(θ), sin(θ) để thực hiện xoay góc, kết hợp với các thành phần tịnh tiến (tx, ty) để giữ tâm xoay cố định tại chính giữa ảnh.</p>
            
            <p><b>Xử lý bù đường viền (Border Handling):</b><br>
            • <b>Constant Black:</b> Điền màu đen vào các khoảng trống sinh ra khi xoay.<br>
            • <b>Replicate:</b> Lặp lại màu của các pixel ở cạnh biên để lấp đầy khoảng trống.<br>
            • <b>Reflect:</b> Phản chiếu đối xứng hình ảnh qua đường biên tạo cảm giác tự nhiên hơn.</p>
            
            <p><b>Hiện tượng cắt góc (Clipping):</b> {clipping_note}</p>
            """
        else:
            x = params.get("x", 0)
            y = params.get("y", 0)
            width = params.get("width", 0)
            height = params.get("height", 0)
            retained = metadata.get("retained_percentage")
            retained_str = f"{retained:.1f}%" if retained is not None else "-"
            html = f"""
            <h3>Thuật toán: Cắt vùng ảnh (Crop by NumPy Slicing)</h3>
            <p><b>Tham số vùng cắt:</b><br>
            • Tọa độ gốc: X = {x}, Y = {y}<br>
            • Kích thước: Chiều rộng = {width}px, Chiều cao = {height}px<br>
            • Tỉ lệ diện tích giữ lại: {retained_str}</p>
            
            <p><b>Khái niệm:</b><br>
            Cắt ảnh là thao tác trích xuất một vùng chữ nhật quan tâm (Region of Interest - ROI) từ ảnh ban đầu và loại bỏ phần còn lại.</p>
            
            <p><b>Triển khai bằng NumPy Slicing:</b><br>
            Trích xuất trực tiếp trên mảng nhiều chiều với cú pháp lát cắt cực nhanh: <code>image[y : y + height, x : x + width]</code>.</p>
            
            <p><b>Hệ tọa độ ảnh số:</b><br>
            • Gốc tọa độ (0, 0) nằm ở góc trên cùng bên trái của ảnh.<br>
            • Trục X tăng dần từ trái sang phải, trục Y tăng dần từ trên xuống dưới.<br>
            • Lưu ý trong mảng NumPy: Chiều thứ nhất là Y (chiều cao), chiều thứ hai là X (chiều rộng).</p>
            
            <p><b>Đánh giá & Ứng dụng thực tế:</b><br>
            Thao tác cắt giúp loại bỏ thông tin nền nhiễu, tập trung vào đối tượng cụ thể (nhận diện khuôn mặt, biển số xe, quét mã QR) và giảm đáng kể thời gian xử lý cho các thuật toán AI/Machine Learning tiếp theo.</p>
            """
        self.text.setHtml(html)
