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
- Dưới đầu cắm còn 9,4 mm tới sàn, chưa đủ cho đầu Dupont: hàn dây trực tiếp vào bo. Mô hình không có chân hàn của bo.
- Rãnh trượt nhạy với bề rộng bo, mà bo các người bán chênh nhau tới khoảng 1 mm. Trước khi in, đo bề rộng bo theo cạnh có hàng chân cắm (mô hình 15,4 mm). Bo rộng 15,4 đến 15,8 mm thì vào vừa: hai thành cứng, không có gì nhún, nên 15,8 mm là sát hết cỡ. Bo hẹp hơn thì khi bo dồn hẳn sang một bên, mép kia chỉ còn nằm dưới rãnh (bề rộng bo − 15,0) mm, ví dụ 0,2 mm với bo 15,2 mm; bo 15,0 mm trở xuống có thể tuột khỏi rãnh. PCB dày 1,6 đến 1,8 mm lọt rãnh. Rãnh đè lên dải 0,6 mm sát hai mép dọc của bo suốt chiều dài bo: dải đó phải trống, đầu chân cắm và mối hàn nằm sâu hơn 0,6 mm tính từ mép.
- Bo không có tiếng tách khi vào và không tự khoá: chỉ có nắp đã đóng mới chặn bo trượt ra. Theo chiều trượt bo xê dịch được 0,8 mm (0,2 mm về phía tường −y, 0,6 mm về phía nắp). Mở nắp là bo trượt ra được. Lực giữ chưa đo.
- Ba khe thoáng rộng 1,6 mm, cao 9 mm, cách nhau 4 mm ở mặt −y; vị trí khe so với chip cảm biến chưa kiểm với bo thật.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở hai mặt âm (−x, −z) bằng keo, đủ số cần cho từng mối ghép. Mặt −y trơn nên không có lỗ. Phía sau lỗ chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Hai rãnh trượt, một ở mỗi thành ±x, mọc từ mặt trong tường −y. Mỗi rãnh gồm một gờ trên đè lên mặt trên PCB suốt chiều dài bo (tới cách tường −y 13,2 mm, khe 0,2 mm) và một gờ dưới đỡ mặt dưới PCB tới cách tường −y 8,9 mm. Hai rãnh nằm cao hơn cổng Ø5 của thành ±x 0,3 mm. Hai khối chặn ở hai góc tường −y chặn bo cách tường 1,0 mm.
- Vị trí bo trong mô hình: mặt dưới PCB cách sàn 11,9 mm, cạnh −y của PCB cách tường 1,2 mm, cạnh +y cách mép gờ nắp 0,6 mm và cách tấm nắp 3,0 mm. Hàng chân cắm ở dưới bo, phía nắp (+y): bo quay đầu chân cắm về phía nắp để thân đầu cắm không chạm gờ dưới khi trượt. Đỉnh chip cách trần 1,4 mm.
- Lắp bo: mở nắp +y, cầm bo mặt chip hướng lên, đầu có hàng chân cắm ở phía bạn. Luồn hai mép dọc của bo vào hai rãnh rồi đẩy bo vào tới khi cạnh trước chạm hai khối chặn. Đóng nắp. Tháo bo: mở nắp rồi kéo bo ra theo rãnh.
- Luồn dây qua cổng Ø5 ở giữa mỗi mặt có điểm nối, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên, cao 17,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 144,0 mm², chạm bàn 277,7 mm²; các cầu của thân đều dưới 0,5 mm². Hai rãnh mọc từ tường −y nằm trên bàn in nên in đứng, không thêm vùng nhô. Slicer cảnh báo nắp: vùng nhô 129,9 mm² khi úp mặt ngoài xuống bàn (chạm bàn 219,6 mm², có bốn cầu 5,1 × 5,1 mm cao 1,5 mm ở lỗ nam châm); hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 113,4 mm² nhưng chỉ chạm bàn 18,9 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
