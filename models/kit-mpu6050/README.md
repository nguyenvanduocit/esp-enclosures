# Module cảm biến MPU6050

Mở trong [app chung](../../#model/kit-mpu6050). Khối 2×2×1 đơn vị (39,8 × 39,8 × 19,8 mm), nắp ở mặt +z. Cả sáu mặt đều có điểm nối, không có mặt trơn.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Cảm biến gia tốc và con quay GY-521 MPU6050 | 1 | Bo khoảng 20,5 × 16 mm theo trang bán hàng (giả định A3 của thiết kế); mô hình thêm thân đầu cắm 20,32 × 2,5 × 2,5 mm dưới bo |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 32) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 8) | Không dùng inox |

## Giả định
- Kích thước bo từ trang bán hàng, các nơi ghi từ 20 × 16 đến 21 × 16,4 mm, chênh nhau khoảng 1 mm; đo bo của bạn trước khi in. Chiều trong của thân là 35,8 × 35,8 mm nên bo lớn hơn vài mm vẫn vừa, nhưng bốn trụ nằm theo kích thước 20,5 × 16 mm.
- Khoảng cách 0,55 mm giữa thân đầu cắm và trụ gần nhất là giả định: mô hình đặt hàng chân cách tâm bo 5 mm theo y, còn kích thước bo các nơi chênh nhau khoảng 1 mm nên vị trí hàng chân thật có thể lệch và khoảng này có thể mất.
- Vị trí lỗ bắt vít của bo không có trong mô hình. Trụ đỡ mặt dưới PCB ở khoảng cách chọn theo kích thước bo, không theo lỗ vít.
- Hàng chân cắm nằm gần cạnh −y của bo, dọc theo chiều dài bo (trục x của mô hình). Mô hình không đánh dấu trục của chip.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau lỗ chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: bo nằm giữa khối, mặt dưới PCB cách sàn 3,9 mm trên bốn trụ Ø2,4 mm đặt ở ±8 mm theo x và ±2 mm theo y so với tâm. Cạnh PCB cách tường trong 7,65 mm theo x và 9,9 mm theo y mỗi bên. Thân đầu cắm treo dưới bo, đáy cách sàn 1,4 mm và cách mép trụ gần nhất 0,55 mm. Với 1,4 mm dưới đáy thân đầu cắm, đầu nối Dupont không lồng được vào chân cắm dưới bo.
- Trụ chỉ đỡ mặt dưới PCB, không có gì giữ bo theo chiều ngang: dán bo bằng keo hoặc băng dính hai mặt.
- Từ đỉnh chip tới tấm nắp còn 9,4 mm (từ mặt trên PCB còn 10,3 mm), đủ cho dây hàn trực tiếp hoặc dải chân cắm ngắn. Gờ nắp bắt đầu ở độ cao 15,4 mm, cao hơn bo.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +z. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +z hướng lên, cao 17,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 678,8 mm², chạm bàn 977,7 mm², có bốn cầu 12,1 × 12,1 mm ở các lỗ vòng đệm mặt −z (cao 1,6 mm); các cầu còn lại đều dưới 1 mm². Slicer cảnh báo nắp: vùng nhô 426,5 mm² khi úp mặt ngoài xuống bàn (chạm bàn 1032,2 mm², có mười sáu cầu 5,1 × 5,1 mm cao 1,5 mm ở lỗ nam châm); hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 316,1 mm² nhưng chỉ chạm bàn 39,7 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
