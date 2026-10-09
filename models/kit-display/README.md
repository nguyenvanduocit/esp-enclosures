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
- Móc gài: thân móc cách mép PCB 0,2 mm mỗi bên, ngạnh đè lên mặt PCB 0,6 mm và cách mặt PCB 0,2 mm. Bo rộng hơn mô hình tới 0,3 mm (đo qua hai cạnh có móc) vẫn vào không phải ép. Bo hẹp hơn 0,3 mm nằm giữa thì mỗi ngạnh còn đè 0,45 mm; nếu bo dồn hẳn sang một bên thì ngạnh bên kia chỉ còn đè 0,1 mm. Lực giữ của móc chưa đo: in thân, gài bo thật và thử trước khi in cả bộ. Ngạnh nằm trên dải 0,6 mm sát mép bo, dài 4 mm ở chỗ mỗi móc; dải đó phải trống, không có linh kiện hay mối hàn nhô quá 0,2 mm. Mô hình không có đầu nối hay chân cắm của bo: nếu chúng nằm ở mặt dưới, sát cạnh ngắn ở khoảng giữa, thì ngạnh vướng vào; xem mặt dưới bo trước khi in. Trước khi in, đo bề dài bo theo cạnh 70,5 mm và tổng chiều dày kính + PCB (mô hình 3,2 + 1,6 = 4,8 mm): tổng này phải không quá 5,2 mm để bo lọt vào ngạnh; mỏng hơn 4,8 mm thì bo lỏng theo chiều cao.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở hai mặt dương (+x, +y) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: mặt kính cách mặt trong của tường +z 0,2 mm, mặt dưới PCB cách sàn 10,8 mm, cạnh −y của PCB cách tường 0,8 mm và cạnh +y cách tấm nắp 11,7 mm. Không có trụ dưới bo: hai ngạnh đỡ mặt dưới PCB, kính tựa vào mặt trong tường +z.
- Hai móc gài, một ở mỗi cạnh ngắn của bo (cạnh ±x). Mỗi móc là một thanh dày 1,2 mm, cao 3 mm, mọc từ mặt trong tường −y, dài 24,5 mm; ngạnh dài 4 mm ở đầu thanh, ngay giữa chiều sâu bo.
- Gài bo: đưa bo vào từ phía nắp +y, mặt kính hướng lên, trượt dưới tường +z cho tới khi cạnh −y chạm tường và vùng hiển thị nằm đúng cửa sổ, rồi đẩy bo thẳng lên. Mép bo đẩy mặt vát của hai ngạnh ra ngoài và hai móc bật vào dưới mặt PCB. Không cần keo. Bo có thể xê dịch 0,4 mm theo chiều cao (khe 0,2 mm dưới ngạnh và 0,2 mm trên kính).
- Tháo bo: gạt phần trên của hai thanh móc (phần cao hơn mặt PCB, giữa mép kính và thanh) ra phía tường x khoảng 0,6 mm bằng tua vít dẹt nhỏ, rồi hạ bo xuống.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên, cao 57,8 mm), nắp úp mặt ngoài xuống bàn in. Hai thanh móc mọc từ tường −y nằm trên bàn in nên in đứng; đầu ngạnh vát 50° về phía gốc nên không thêm vùng nhô. Thân có vùng nhô 946,6 mm², trong đó có bốn cầu 12,1 × 12,1 mm ở các lỗ vòng đệm mặt −y (cao 1,6 mm) và một cầu 2,0 × 48,96 mm ở mép trên cửa sổ (cao 42,8 mm). Slicer cảnh báo nắp: vùng nhô 452,4 mm² khi úp mặt ngoài xuống bàn; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 207,6 mm² nhưng chỉ chạm bàn 18,9 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
