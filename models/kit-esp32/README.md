# Module ESP32-C3 mini

Mở trong [app chung](../../#model/kit-esp32). Khối 2×2×2 đơn vị (39,8 × 39,8 × 39,8 mm), nắp ở mặt +y.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| ESP32-C3 SuperMini | 1 | 18 × 22,5 mm, chân hàn xuống |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 48) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 12) | Không dùng inox |

## Giả định
- Kích thước bo từ trang bán hàng; đo bo của bạn trước khi in.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.
- Hai hàng chân header hàn xuống, nằm ngoài các trụ (thân nhựa header cách mép trụ chỉ 0,25 mm theo trục x, chân kim loại cách 1,2 mm; kích thước board lệch khoảng 0,5 mm giữa các người bán nên đo header thật trước khi in) và dài 8,5 mm dưới PCB, còn cách sàn 6,2 mm.
- Khe USB-C rộng 12 mm, cao 6 mm, thừa hơn đầu cắm 9 × 3,2 mm của bo; ốp lưng cáp quá to có thể không vừa.
- Móc gài: thân móc cách mép PCB 0,2 mm mỗi bên, ngạnh đè lên mặt PCB 0,6 mm và cách mặt PCB 0,2 mm. Bo rộng hơn mô hình tới 0,3 mm (đo qua hai cạnh có móc) vẫn vào không phải ép. Bo hẹp hơn 0,3 mm nằm giữa thì mỗi ngạnh còn đè 0,45 mm; nếu bo dồn hẳn sang một bên thì ngạnh bên kia chỉ còn đè 0,1 mm. Lực giữ của móc chưa đo: in thân, gài bo thật và thử trước khi in cả bộ. Ngạnh nằm trên dải 0,6 mm sát mép bo, dài 4 mm ở chỗ mỗi móc; dải đó phải trống, không có linh kiện hay mối hàn nhô quá 0,2 mm. Chân header gần nhất cách mũi ngạnh 0,46 mm theo x: nếu mối hàn chân header lan ra gần mép bo thì ngạnh tì lên mối hàn. Trước khi in, đo bề rộng bo qua hai cạnh dài (mô hình 18 mm) và độ dày PCB (mô hình 1,6 mm; dày quá 1,8 mm thì không lọt dưới ngạnh).

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Hướng mặt: cổng USB-C quay ra mặt −y, đối diện nắp (+y). Khe USB-C nằm trong dải giữa hai hàng lỗ khoét của mặt đó.
- Hai móc gài, một ở mỗi cạnh dài của bo (cạnh ±x). Mỗi móc là một thanh dày 1,2 mm mọc từ mặt trong tường −y, dài 15,3 mm, ngạnh dài 4 mm ở đầu thanh, ngay giữa chiều dài bo.
- Gài bo: đưa bo vào từ phía nắp +y, mặt linh kiện hướng lên, USB-C sát khe, rồi ấn bo thẳng xuống bốn trụ. Mép bo đẩy mặt vát của hai ngạnh ra ngoài và hai móc bật lại khi bo chạm trụ. Không cần keo.
- Tháo bo: gạt đầu hai thanh móc (phía nắp) ra phía tường x khoảng 0,6 mm bằng móng tay hoặc tua vít dẹt nhỏ, rồi nhấc bo lên.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên), nắp úp mặt ngoài xuống bàn in. Thân cao 37,8 mm, nắp cao 4,4 mm. Hai thanh móc mọc từ tường −y nằm trên bàn in nên in đứng; đầu ngạnh vát 50° về phía gốc nên không thêm vùng nhô (thân vẫn 1000,5 mm²). Slicer cảnh báo nắp: vùng nhô 426,5 mm² khi úp mặt ngoài xuống bàn; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 316,5 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
