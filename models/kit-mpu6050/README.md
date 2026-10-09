# Module cảm biến MPU6050

Mở trong [app chung](../../#model/kit-mpu6050). Khối 2×2×1 đơn vị (39,8 × 39,8 × 19,8 mm), nắp ở mặt +z. Cả sáu mặt đều có điểm nối, không có mặt trơn.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Cảm biến gia tốc và con quay GY-521 MPU6050 | 1 | Bo khoảng 20,5 × 16 mm theo trang bán hàng (giả định A3 của thiết kế); mô hình thêm thân đầu cắm 20,32 × 2,5 × 2,5 mm dưới bo |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 32) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 8) | Không dùng inox |

## Giả định
- Các trang bán hàng ghi bo từ 20 × 16 đến 21 × 16,4 mm. Thân chỉ chứng minh được bo 20,2 đến 20,8 × 15,7 đến 16,3 mm (mô hình 20,5 × 16 mm ±0,3 mm). Bo rộng 16,4 mm chạm sát hai khối chặn và bo 21 mm vượt khoảng đã kiểm; bo dài dưới 20,2 mm có thể tuột khỏi móc khi dồn về một bên. Đo bo của bạn trước khi in.
- Khoảng cách 0,55 mm giữa thân đầu cắm và trụ gần nhất là giả định: mô hình đặt hàng chân cách tâm bo 5 mm theo y, còn kích thước bo các nơi chênh nhau khoảng 1 mm nên vị trí hàng chân thật có thể lệch và khoảng này có thể mất.
- Vị trí lỗ bắt vít của bo không có trong mô hình. Trụ đỡ mặt dưới PCB ở khoảng cách chọn theo kích thước bo, không theo lỗ vít.
- Hàng chân cắm nằm gần cạnh −y của bo, dọc theo chiều dài bo (trục x của mô hình). Mô hình không đánh dấu trục của chip.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.
- Móc gài: thân móc cách mép PCB 0,1 mm mỗi bên, ngạnh đè lên mặt PCB 0,8 mm và cách mặt PCB 0,2 mm. Bộ kiểm tra chứng minh bo dài 20,2 đến 20,8 mm (qua hai cạnh có móc) và rộng 15,7 đến 16,3 mm, tức kích thước mô hình ±0,3 mm. Bo lớn hơn tới 0,3 mm đẩy móc ra và vẫn gài được (chân móc giãn 1,34 % khi gài). Bo nhỏ hơn tới 0,3 mm, dù dồn hẳn về một phía, vẫn còn ít nhất 0,4 mm dưới ngạnh bên kia và xê dịch không quá 1 mm. Bo ngoài khoảng này chưa được kiểm. Theo y, hai khối chặn đứng cách mép bo 0,2 mm. Lực giữ của móc chưa đo: in thân, gài bo thật và thử trước khi in cả bộ. Ngạnh nằm trên dải 0,8 mm sát mép bo, dài 4 mm ở chỗ mỗi móc; dải đó phải trống, không có linh kiện hay mối hàn nhô quá 0,2 mm. Trước khi in, đo bề dài bo theo cạnh 20,5 mm, bề rộng (16 mm) và độ dày PCB (mô hình 1,6 mm; dày quá 1,8 mm thì không lọt dưới ngạnh).

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau lỗ chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: bo nằm giữa khối, mặt dưới PCB cách sàn 9,1 mm trên bốn trụ Ø2,4 mm đặt ở ±8 mm theo x và ±2 mm theo y so với tâm. Cạnh PCB cách tường trong 7,65 mm theo x và 9,9 mm theo y mỗi bên. Thân đầu cắm treo dưới bo, đáy cách sàn 6,6 mm và cách mép trụ gần nhất 0,55 mm. Mô hình có tám chân cắm 11,5 mm hàn chân dài xuống: đầu chân dưới cách sàn 0,6 mm, đầu chân trên nhô 1,4 mm trên mặt PCB. Đầu nối Dupont không lồng được vào chân dưới bo.
- Bo đặt cao 9,1 mm trên sàn để chân cắm 8,5 mm dưới bo còn cách sàn 0,6 mm, và để thân móc dày 1,0 mm uốn trên 10,3 mm (từ sàn tới mặt dưới ngạnh, trừ góc bo 0,6 mm ở chân). Bo lớn hơn 0,3 mm làm chân móc giãn 1,34 % khi gài.
- Hai móc gài, một ở mỗi cạnh ngắn của bo (cạnh ±x), mọc thẳng từ sàn ở giữa cạnh, rộng 4 mm, dày 1,0 mm, chân bo tròn 0,6 mm cả hai mặt, đỉnh ở độ cao 14,2 mm.
- Hai khối chặn đứng trên sàn ở giữa hai cạnh dài của bo (cạnh ±y), rộng 4 mm, cách mép PCB 0,2 mm, cao tới mặt trên PCB; bo xê dịch được 0,2 mm mỗi chiều.
- Gài bo: đặt bo lên bốn trụ, mặt chip hướng lên, rồi ấn thẳng xuống. Mép bo đẩy mặt vát của hai ngạnh ra ngoài và hai móc bật lại khi bo chạm trụ. Không cần keo.
- Tháo bo: gạt đỉnh hai móc ra phía tường x khoảng 0,6 mm bằng móng tay rồi nhấc bo lên.
- Từ đầu trên của chân cắm tới tấm nắp còn 3,7 mm, từ đỉnh chip còn 4,2 mm, từ mặt trên PCB còn 5,1 mm. Gờ nắp bắt đầu ở độ cao 15,4 mm, cao hơn bo và móc.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +z. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +z hướng lên, cao 17,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 686,0 mm², chạm bàn 977,7 mm², có bốn cầu 12,1 × 12,1 mm ở các lỗ vòng đệm mặt −z (cao 1,6 mm). Mặt dưới hai ngạnh là hai gờ 0,9 × 4 mm in treo ở độ cao 12,9 mm (3,6 mm² mỗi gờ, thêm 7,2 mm² so với thân không móc); các cầu còn lại đều dưới 1 mm². Slicer cảnh báo nắp: vùng nhô 426,5 mm² khi úp mặt ngoài xuống bàn (chạm bàn 1032,2 mm², có mười sáu cầu 5,1 × 5,1 mm cao 1,5 mm ở lỗ nam châm); hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 316,1 mm² nhưng chỉ chạm bàn 39,7 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
