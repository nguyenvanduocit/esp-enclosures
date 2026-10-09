# Module cảm biến BME280

Mở trong [app chung](../../#model/kit-bme280). Khối 1×1×1 đơn vị (19,8 × 19,8 × 19,8 mm), nắp ở mặt +y. Mặt −y là mặt trơn có ba khe thoáng, không có điểm nối.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Cảm biến GY-BME280 (nhiệt độ, độ ẩm, áp suất) | 1 | Bo 15,4 × 11,6 mm theo trang bán hàng (giả định A3 của thiết kế); mô hình thêm thân đầu cắm 15,24 × 2,5 × 2,5 mm dưới bo |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 12) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 2) | Không dùng inox |

## Giả định
- Kích thước bo từ trang bán hàng; đo bo của bạn trước khi in.
- Chiều rộng trong của thân là 15,8 mm cho bo rộng 15,4 mm: còn 0,4 mm cho cả hai bên (0,2 mm mỗi bên khi bo nằm giữa). Bo rộng hơn sẽ không vừa; khi đó phải đổi sang khối 2×1×1.
- Dưới đầu cắm chỉ còn 4,2 mm tới sàn, không đủ cho đầu Dupont: hàn dây trực tiếp vào bo. Mô hình không có chân hàn của bo.
- Ba khe thoáng rộng 1,6 mm, cao 9 mm, cách nhau 4 mm ở mặt −y; vị trí khe so với chip cảm biến chưa kiểm với bo thật.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở hai mặt âm (−x, −z) bằng keo, đủ số cần cho từng mối ghép. Mặt −y trơn nên không có lỗ. Phía sau lỗ chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: mặt dưới PCB cách sàn 6,7 mm trên hai trụ Ø2,4 mm đặt lệch 5,5 mm về hai phía của tâm theo x, cách mặt trong tường −y 9,4 mm. Cạnh −y của PCB cách tường 1,2 mm, cạnh +y cách mép gờ nắp 0,6 mm và cách tấm nắp 3,0 mm. Trụ chỉ đỡ mặt dưới PCB, không có gì giữ bo theo chiều ngang: dán bo bằng keo hoặc băng dính hai mặt.
- Luồn dây qua cổng Ø5 ở giữa mỗi mặt có điểm nối, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên, cao 17,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 168,8 mm², chạm bàn 277,7 mm²; các cầu của thân đều dưới 0,5 mm². Slicer cảnh báo nắp: vùng nhô 129,9 mm² khi úp mặt ngoài xuống bàn (chạm bàn 219,6 mm², có bốn cầu 5,1 × 5,1 mm cao 1,5 mm ở lỗ nam châm); hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 113,4 mm² nhưng chỉ chạm bàn 18,9 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
