# Module màn hình 2.4"

Mở trong [app chung](../../#model/kit-display). Khối 4×3×1 đơn vị (79,8 × 59,8 × 19,8 mm), nắp ở mặt +y. Mặt +z là mặt màn hình, trơn và không có điểm nối.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Màn hình TFT 2.4" ILI9341 | 1 | Bo 70,5 × 43,3 mm, vùng hiển thị 48,96 × 36,72 mm (giả định A1 của thiết kế) |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 28) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 19) | Không dùng inox |

## Giả định
- Kích thước bo và vùng hiển thị theo giả định A1; đo màn hình của bạn trước khi in.
- Kính 60 × 40 × 3,2 mm là giả định, không có trong trang bán hàng. Cửa sổ cắt đúng 48,96 × 36,72 mm, bằng vùng hiển thị và không chừa lề (thiết kế gọi là 49 × 37 mm, làm tròn); nếu kính căn giữa dưới cửa sổ thì phủ lên tường mặt +z mỗi bên 5,5 mm theo x và 1,6 mm theo y.
- Chiều dài trong của thân theo x là 75,8 mm cho bo dài 70,5 mm: còn 5,3 mm cho cả hai bên (2,65 mm mỗi bên khi bo nằm giữa).
- Mô hình không có chân cắm hay cáp của bo; dây đi qua cổng Ø5 ở giữa mỗi đơn vị trên năm mặt có điểm nối (mặt +z trơn nên không có cổng).
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở hai mặt dương (+x, +y) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: mặt kính cách mặt trong của tường +z 0,2 mm, mặt dưới PCB cách sàn 10,8 mm, cạnh −y của PCB cách tường 0,8 mm và cạnh +y cách tấm nắp 11,7 mm. Không có trụ đỡ nào dưới bo: bo lơ lửng trên sàn và chỉ được giữ bằng keo.
- Lắp bo từ phía nắp +y, mặt kính hướng lên, trượt dưới tường +z cho tới khi vùng hiển thị nằm đúng cửa sổ. Dán viền kính vào mặt trong tường +z.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên, cao 57,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 946,6 mm², trong đó có bốn cầu 12,1 × 12,1 mm ở các lỗ vòng đệm mặt −y (cao 1,6 mm) và một cầu 2,0 × 48,96 mm ở mép trên cửa sổ (cao 42,8 mm). Slicer cảnh báo nắp: vùng nhô 452,4 mm² khi úp mặt ngoài xuống bàn; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 207,6 mm² nhưng chỉ chạm bàn 18,9 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
