# Module cảm biến PIR

Mở trong [app chung](../../#model/kit-pir). Khối 2×2×2 đơn vị (39,8 × 39,8 × 39,8 mm), nắp ở mặt −z. Mặt +z là mặt trơn có lỗ Ø24,4 mm cho thấu kính, không có điểm nối; năm mặt còn lại đều có điểm nối.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Cảm biến chuyển động HC-SR501 | 1 | Bo 32 × 24 mm, thấu kính Ø23 mm theo trang bán hàng (giả định A3 của thiết kế); mô hình thêm thân đầu cắm 7,62 × 2,5 × 2,5 mm dưới bo |
| Nam châm tròn 5×1,5 | 32 khi lắp kín (4 mỗi mối ghép) | Ở hai mặt +x và +y; Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 12 khi lắp kín (1 mỗi mối ghép) | Ở ba mặt −x, −y, −z; không dùng inox |

## Giả định
- Kích thước bo và thấu kính từ trang bán hàng, các nơi ghi chênh nhau khoảng 1 mm; đo bo của bạn trước khi in. Chiều trong của thân là 35,8 × 35,8 mm nên bo 32 × 24 mm còn 1,9 mm mỗi bên theo x và 5,9 mm mỗi bên theo y.
- Chiều cao thấu kính: mô hình giả định 18 mm trên mặt trên PCB (cao tổng 19,2 mm tính từ mặt dưới PCB). Các trang bán hàng ghi tổng chiều cao từ 18 đến 30 mm, không khớp nhau. Đỉnh thấu kính trong mô hình nằm 0,9 mm dưới mặt ngoài +z; thấu kính cao quá 18,9 mm trên mặt PCB thì nhô ra khỏi mặt +z. Đo thấu kính của bạn trước khi in.
- Lỗ Ø24,4 mm cho thấu kính Ø23 mm: còn 0,7 mm mỗi bên khi bo nằm giữa.
- Biến trở và jumper của bo không có trong mô hình; mô hình chỉ có PCB, thấu kính và thân đầu cắm dưới bo (tâm cách tâm bo +12 mm theo x và −9 mm theo y).
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.
- Móc gài: thân móc cách mép PCB 0,2 mm mỗi bên, ngạnh đè lên mặt PCB 0,6 mm và cách mặt PCB 0,2 mm. Bo rộng hơn mô hình tới 0,3 mm (đo qua hai cạnh có móc) vẫn vào không phải ép. Bo hẹp hơn 0,3 mm nằm giữa thì mỗi ngạnh còn đè 0,45 mm; nếu bo dồn hẳn sang một bên thì ngạnh bên kia chỉ còn đè 0,1 mm. Lực giữ của móc chưa đo: in thân, gài bo thật và thử trước khi in cả bộ. Ngạnh nằm trên dải 0,6 mm sát mép bo, dài 4 mm ở chỗ mỗi móc; dải đó phải trống, không có linh kiện hay mối hàn nhô quá 0,2 mm. Mô hình không có linh kiện mặt dưới của bo (biến trở, jumper, IC): xem mặt dưới bo ở giữa hai cạnh dài trước khi in. Trước khi in, đo bề rộng bo theo cạnh 24 mm và độ dày PCB (mô hình 1,2 mm; dày quá 1,4 mm thì không lọt trên ngạnh).

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở hai mặt dương (+x, +y) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau lỗ chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Vị trí bo trong mô hình: mặt dưới PCB cách mặt ngoài −z 19,7 mm, mặt trên PCB cách 20,9 mm, mặt dưới trần cách 37,8 mm. Bo treo từ trần bằng bốn trụ Ø3 mm đặt ở ±13 mm theo x và ±9 mm theo y so với tâm; mỗi trụ dài 17,4 mm, đầu dưới chạm mặt trên PCB, đầu trên cắm sâu 0,5 mm vào trần. Mép trụ cách mép PCB 1,5 mm và cách thấu kính 2,8 mm.
- Trụ chỉ định độ cao của mặt trên PCB. Hai móc gài, một ở mỗi cạnh dài của bo (cạnh ±y), treo từ trần, rộng 4 mm, dày 1,2 mm, dài 19,5 mm; ngạnh ở đầu dưới đỡ mặt dưới PCB. Hai móc lệch 6 mm khỏi tâm theo x, đối xứng qua tâm (móc +y ở phía +x, móc −y ở phía −x), để gốc móc cách lỗ thấu kính 0,6 mm.
- Tháo bo: mở nắp −z, gạt đầu dưới hai móc ra phía tường y khoảng 0,6 mm và đỡ bo khi nó rơi ra.
- Thân đầu cắm dưới bo có đáy cách mặt ngoài −z 17,2 mm, cách mặt trên của nắp 12,8 mm. Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt có điểm nối.
- Lắp từ phía −z: đưa thấu kính vào lỗ, rồi đẩy bo thẳng lên cho tới khi mặt trên PCB chạm bốn trụ. Mép bo đẩy mặt vát của hai ngạnh ra ngoài và hai móc bật vào dưới mặt PCB. Không cần keo. Đóng nắp −z. Nắp có gờ lồng vào thân, không cần vít.
- In: thân in với mặt trơn +z úp xuống bàn, nên lỗ thấu kính nằm xuyên qua các lớp đầu. Hướng này có vùng nhô 501,7 mm², chạm bàn 970,0 mm², cao 37,8 mm. Hai móc mọc từ trần nằm trên bàn in nên in đứng; mặt trên hai ngạnh là hai gờ 0,8 × 4 mm in treo ở độ cao 20,3 mm (3,2 mm² mỗi gờ, thêm 6,4 mm² so với thân không móc); các cầu còn lại của thân đều dưới 1 mm². Nắp úp mặt ngoài xuống bàn có vùng nhô 481,1 mm², chạm bàn 977,7 mm², cao 4,4 mm, có bốn cầu 12,1 × 12,1 mm cao 1,6 mm ở các lỗ vòng đệm; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 257,4 mm² nhưng chỉ chạm bàn 40,4 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
