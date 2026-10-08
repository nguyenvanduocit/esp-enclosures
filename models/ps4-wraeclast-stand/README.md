# PS4 · Phế tích Wraeclast

Giá dựng đứng cho PS4 đời đầu (CUH-1000A), trang trí như một phế tích gothic tối màu: tường cửa sổ vòm nhọn bị vỡ khắc rune, cột bát giác đội sọ có hàm, xích sắt nặng gãy mắt cuối, và hai bàn tay xương nằm ngửa đỡ tay cầm DualShock 4 trên bệ đá. Máy đứng trên mặt hông hẹp, kẹp giữa hai cụm đế giống hệt nhau đặt ở nửa trước và nửa sau máy; mỗi cụm có một bàn tay xương đứng sát bên. Rune, mạch vữa, sọ, xích, vết vỡ và vết bào mòn đều sinh bằng code trong `model.py`, dùng các hàm thuần trong `printkit/art.py`. Không dùng mesh, logo hay chữ lấy từ game.

Mở model trong [app chung](../../#model/ps4-wraeclast-stand); bản ZIP có `index.html` chạy offline. Chế độ **Tháo lắp** gỡ sọ, xích và nhấc tay cầm ra cùng lúc, trượt bệ tay cầm ra ngoài, nhấc máy, nâng cột khỏi hốc, rồi lắp lại theo thứ tự ngược. Sidebar có **Hiển thị** để ẩn từng chi tiết (ẩn PS4 thì số đo chiều cao đổi sang chiều cao giá), **Đo** để bật kích thước, **In & tải** để lấy file và cấu hình in.

## In coupon trước

`fitCoupon.stl` là một lát của đế: một gân đỡ, hai vách kẹp và rãnh gió, nặng khoảng 22 g. In nó trước rồi đặt thử lên máy thật. Máy phải lọt khe 54 mm, nằm êm trên gân và không chạm đáy rãnh gió. Chỉ in hai đế (≈ 110 g/cái) khi coupon đã vừa. Nếu quá chặt hoặc quá lỏng, chỉnh bù biên XY hoặc flow của máy in; không scale STL vì sẽ làm sai hốc cột và chốt sọ.

## Kéo từng chi tiết

Rê chuột lên chi tiết để làm sáng nó và hiện mũi tên, rồi kéo theo mũi tên. Đế đi xuống; tường cửa sổ, cột bát giác, sọ và PS4 đi lên; xích trượt ra khỏi móc theo phương ngang; bệ tay cầm trượt ra xa máy; tay cầm đi lên theo trục nghiêng 70°. Đây là thao tác minh họa, không mô phỏng va chạm khi kéo: kéo tay cầm quá 26 mm khi sọ còn tại chỗ thì hình tay cầm đi xuyên qua sọ.

## Máy và giả định

| Thông số | Giá trị dùng trong CAD | Nguồn / độ chắc chắn |
|---|---|---|
| PS4 CUH-1000A | 275 × 53 × 305 mm, 2,8 kg | HIGH: thông số kỹ thuật trên playstation.com |
| Hình bao máy khi đứng | Hộp 53 × 305 × 275 mm, đáy ở z = 20 mm, mặt trước (khe đĩa) hướng −Y | HIGH: hộp bao trọn tiết diện hình bình hành nên mọi kiểm tra khe hở đều thiên về an toàn |
| Lỗ hút gió | Hai mặt hông hẹp (305 × 53), thoát nhiệt phía sau | MEDIUM: tổng hợp từ blog và diễn đàn; **vị trí lưới hút trên mặt hông chưa đo** |
| Trọng tâm máy | Tâm hộp bao, z = 157,5 mm | MEDIUM: giả định, chưa cân thực tế |
| Máy in | Bambu A1 / P1S / X1C, 256³ mm, nozzle 0,4 mm, PLA | HIGH: người dùng |
| Chân cao su | Loại dán Ø12 mm, dày hơn 1,5 mm | LOW: chưa chọn loại cụ thể |
| Tay cầm DualShock 4 | Hộp bao 162 × 57 × 100 mm, 210 g; chỉ dùng hộp, không theo đường cong thật | MEDIUM: số công bố dao động 161–162 × 52–57 × 98–100 mm, CAD lấy số lớn nhất |

**HIGH:** hình học và các kiểm tra trong `verification.json` đã chạy. **MEDIUM:** vị trí lưới hút gió, trọng tâm máy, hình bao tay cầm. **LOW:** độ vừa với máy thật và tải trọng, vì chưa in thử (`physical_fit_tested: false`) và không có tính toán FEA.

## Cấu tạo

- **Đế** 170 × 80 mm, hai bậc cao 10 mm. Hai vách kẹp cao tới 65 mm; đỉnh vỡ thấp nhất đo được 56,7 mm. Khe giữa rộng 54 mm (máy 53 mm, hở 0,5 mm mỗi bên) cắt suốt chiều sâu xuống còn sàn 6 mm, tạo rãnh gió cao 14 mm dưới máy. Hai gân rộng 8 mm đỡ máy ở cao độ 20 mm. Hai hốc cột sâu 6 mm: 34,4 × 66,4 mm cho tường cửa sổ và 34,4 × 34,4 mm cho cột bát giác. Mặt ngoài hai vách kẹp có mạch vữa (3 hàng, rộng 1 mm, sâu 1,5 mm tính từ mặt danh nghĩa). Mặt dưới có 4 hõm Ø12 × 1,5 mm cho chân cao su. Mặt trước bậc dưới khắc một dải rune.
- **Tường cửa sổ** (`pillar.stl`) dày 30 × rộng 66 mm, đặt ở phía +X. Chân 34 × 66 × 6 mm cắm hốc; đai chân 38 × 70 mm vát 2 mm đặt lên mặt đế. Mặt +X của phần thân thấp (z 18–58 mm) khắc 3 rune 22 mm, nét 2,2 mm, sâu 1,4 mm; trên đó là gờ ngang rồi hai cửa sổ vòm nhọn (rộng 19 mm, cao 66–151,5 mm, trụ giữa 9 mm) và một hoa bốn thùy xuyên tường ở trên cửa sổ −Y. Cột bên −Y còn nguyên và đội tháp nhọn đỉnh ở z = 222,5 mm (đo từ đáy hốc; 236,5 mm tính từ mặt bàn). Phía +Y bị vỡ chéo qua cửa sổ thứ hai, điểm thấp nhất của vết vỡ z ≈ 98 mm; 5–8 vết mẻ sâu tối đa 5 mm trên bốn mặt. Mạch vữa rộng 1 mm, sâu 1,5 mm tính từ mặt danh nghĩa (bào mòn lấy tối đa 1 mm trước), cách nhau 14 mm, chạy trên mặt +X (từ z = 66 mm), mặt −X (trừ gờ ngang z 58–64 mm) và hai đầu. Móc treo xích Ø6 × 22 mm ở z = 160 mm, có gân 45° bên dưới.
- **Cột bát giác** (`stub.stl`) 30 mm giữa hai mặt song song, chân đế loe từ 34 mm, đầu cột loe lên 35 mm, cao 100 mm, mặt ngồi phẳng tuyệt đối ở z = 100 mm (diện tích phẳng ≈ 778 mm²). Tám rãnh dọc rộng 4,4 mm, sâu 1,2 mm và hai vòng rãnh quanh thân. Các vết mẻ chỉ làm thấp mép đầu cột, không bao giờ nhô lên trên mặt ngồi. Chốt Ø8 × 6 mm giữ sọ.
- **Sọ** có hàm, khoảng 54 × 65 × 79 mm, nhìn ra ngoài, đứng trên đoạn cột sống ngắn mang lỗ Ø8,4 × 7 mm cắm vào chốt. Có gờ mày chéo, hốc mắt sâu nghiêng, mũi, gò má, cung gò má, hàm dưới hé 2,3 mm, hai hàng răng, một vết nứt dọc trán và một mảng vỡ trên đỉnh. Sọ liền một khối; khe giữa các răng rộng ≈ 1,2 mm.
- **Xích** 6 mắt, dây Ø5 mm, lòng mắt rộng 10 mm (móc Ø6 hở 2 mm mỗi bên). Các mắt chồng nhau 0,4 mm nên cả xích in thành một khối. Mắt cuối có khe gãy 2 mm.

- **Bệ tay cầm** 94 × 182 mm, đặt ở phía cột bát giác (−X), sát đầu đế. Tay cầm nghiêng 70° so với mặt bàn, mặt hướng ra ngoài, đầu có cổng micro-USB hướng về đế. Đáy tay cầm tì lên mặt ngồi nghiêng 20° (khối đặc bên dưới); lưng tựa dày 8 mm chỉ cao 60% chiều dài tay cầm nên cổng sạc vẫn thông. Gờ chặn cao 10 mm, hở 1 mm trước tay cầm; hai má là trụ gãy dày 8 mm, hở 2 mm, đỉnh vỡ cao tối đa 60 mm. Mặt ngoài bậc đáy khắc dải rune; mặt dưới có 4 hõm chân cao su. Mộng 39,6 × 19,8 × 5,6 mm ở đầu +X cắm vào hốc dưới đầu −X của đế (hở 0,2 mm). Mộng chỉ định vị: bệ đứng riêng trên chân cao su của nó và tự chịu tải.
- **Bàn tay xương** nằm ngửa trên mặt bàn, trước vách trước của bệ: bốn ngón xòe, mỗi ngón ba đốt theo tỷ lệ 1 : 0,8 : 0,7 như tay thật (ngón giữa dài nhất, 45 + 28 + 20 mm; ngón út ngắn nhất, 31 + 17 + 17 mm), xương hình tạ với thân Ø8,4–10 mm ở hai đốt đầu và Ø6,8–8,5 mm ở đốt cuối (thu 0,85 lần), đầu khớp loe khoảng 1,2–1,4 lần, hai đốt sau cong lên (đốt giữa nghiêng 32° so với mặt bàn, đốt cuối dựng gần thẳng đứng, 86°, ngả 4° về phía vách) (điểm cao nhất của xương cao 44 mm so với mặt bàn). Ngón cái (Ø11,6 mm, ba đốt 30 + 23 + 19 mm) xòe ra từ má +Y. Gốc các ngón nằm 2,2 mm trong vách trước của bệ, nên bệ đá là lòng bàn tay; xương không bị bào mòn, lưới 1,2 mm và `simplify(0.2)` để cả bệ còn dưới 60.000 tam giác (52.724).

Hai bộ dùng chung một bộ STL; bộ sau là bộ trước xoay 180° quanh trục đứng. Hai cụm đế nằm trong y = ±52,5…132,5 mm, không che cổng trước, cổng sau và lỗ thoát nhiệt. Bệ đá chiếm x = ±86…180 mm, cách vùng cổng 1 mm; các ngón tay xương vươn tới x = ±251 mm (ngón dài nhất 93 mm) và ngón cái tới y = 158,9 mm trong tọa độ cụm (66,4 mm ở tọa độ thế giới), đều ngoài vùng cổng; ngón út đi tới y = −141,5 mm thế giới, còn mép −Y của bệ đá (−151,5 mm) cách vùng cổng 1 mm.

**Lấy tay cầm:** nhấc lên khỏi gờ chặn (hơn 10 mm theo trục nghiêng) rồi kéo ra phía ngoài. Nhấc thẳng theo trục nghiêng chỉ đi được 26 mm rồi chạm sọ, vì trục này hướng về phía cột bát giác.

## File in và tái tạo

- `fitCoupon.stl`: coupon thử khe, đáy xuống bàn, in đầu tiên.
- `plinth.stl`: đế, in 2 cái, đáy xuống bàn. Hõm chân cao su là cầu Ø12 mm, hốc mộng ở đầu −X là cầu rộng 40 mm; chỉ bật support ở các vùng đó nếu cầu bị võng.
- `pillar.stl`: tường cửa sổ, in 2 cái, đứng thẳng. Cung cửa sổ là vòm nhọn và móc xích có gân 45°, không cần support; nên dùng brim 5 mm vì tường cao 222 mm.
- `stub.stl`: cột bát giác, in 2 cái, đứng thẳng, không cần support (đầu cột loe 2,5 mm mỗi bên trên 10 mm chiều cao, nghiêng 14° so với phương đứng).
- `skull.stl`: sọ, in 2 cái, đáy phẳng xuống bàn. **Cần tree support** cho mái hốc mắt, mặt dưới gò má, hàm, hai hàng răng và phần dưới hộp sọ: `verification.json` đo được 2.980 mm² mặt dốc hơn 45°. `printkit cad` cảnh báo `skull: set print_rotation to (90, 0, 0)`; hướng đó bỏ mất đáy phẳng chạm bàn nên giữ nguyên hướng đứng.
- `altar.stl`: bệ tay cầm cùng bàn tay xương, in 2 cái, đáy xuống bàn, **cần tree support** dưới các ngón: `verification.json` đo được 1.239 mm² mặt dốc hơn 45° cho cả bệ, gồm ≈ 450 mm² là trần 4 hõm chân cao su (4 × 113 mm²), ≈ 690 mm² dưới các ngón (hầu hết ở độ cao 0–20 mm, dưới đốt giữa nghiêng 32°; đốt cuối dựng gần thẳng đứng nên gần như không cần đỡ) và ≈ 115 mm² ở phần đá còn lại. Mộng nằm sát bàn nên in được không cần đỡ. Xem gờ chặn và rãnh rune trong Preview.
- `chain.stl`: xích, in 2 cái, nằm ngang với các mắt nghiêng ±45°, điểm thấp nhất chạm bàn. **Cần tree support** (1.086 mm² mặt dốc hơn 45°); gỡ nhẹ tay. `printkit cad` cảnh báo `chain: set print_rotation to (0, 0, -45)` vì hướng đó (xích treo thẳng đứng như khi lắp) chỉ còn khoảng 416 mm² overhang. Nhưng nó dựng xích cao 132 mm trên một điểm, diện tích chạm bàn 0 mm² (`orientations` trong `verification.json`), nên không in được. Bảng xếp hạng hướng in của printkit chưa loại hướng không chạm bàn; giữ nguyên hướng nằm ngang, các mắt nghiêng ±45°.
- `assembly.step`: chỉ chứa phần cơ khí của hai bộ ở vị trí lắp: đế, tường cửa sổ, cột bát giác, xích, bệ tay cầm, tổng 10 solid, trước khi bào mòn, không có sọ và tay cầm. Đây là file để sửa kích thước. File STEP không giống hệt từng byte giữa các lần chạy (có dấu thời gian), nên sau mỗi lần `printkit cad` cần chạy lại `printkit build` để ZIP khớp với thư mục.
- `model.py`: nguồn duy nhất: CadQuery cho phần cơ khí, SDF của sọ, bảng rune, mạch vữa, xích, và toàn bộ `@model.check`. Hàm SDF, bào mòn và lưới chuẩn tắc dùng chung nằm trong `printkit/art.py`.
- `reference/ds4.stl`, `reference/ds4Back.stl`: hộp bao tay cầm nghiêng 20°, chỉ để xem.
- `model.json`, `verification.json`: sinh ra, không sửa tay. `model.json` theo [schema chung](../../model.schema.json).

```sh
uv run printkit cad ps4-wraeclast-stand   # khoảng 1 phút
uv run printkit build
```

Quy trình cho mỗi chi tiết đá như sau. CadQuery dựng phôi, kể cả các nhát cắt vỡ và vết mẻ với seed cố định. `art.erode` chia lưới khoảng 0,8 mm rồi đẩy từng đỉnh **chỉ vào trong**, sâu tối đa 1 mm theo pháp tuyến đã làm mượt. Lớp 1 mm sát mặt bàn và các vùng che (chân tường và cột, mặt khắc rune, mặt trước dải rune, mặt tường quay vào máy) không bị đẩy. Sau bước này là `simplify(0.05)`. Cuối cùng mới cắt các phần chính xác: khe máy, đỉnh gân, hốc cột, hốc mộng, hõm chân cao su, rãnh rune, mạch vữa, hai cửa sổ vòm nhọn và hoa bốn thùy của tường, rãnh dọc của cột bát giác, mặt ngồi cột bát giác, mặt ngồi, lưng tựa và gờ chặn của bệ; và ghép các phần chính xác: chân tường 34 × 66 mm và chân cột 34 mm, móc xích, chốt sọ, mộng bệ. Phôi bệ đắp dư 3 mm vào chỗ tay cầm và lên mặt trên, mặt ngoài của gờ chặn, để nhát cắt cuối tạo ra mặt ngồi, lưng tựa và cả ba mặt của gờ chặn chính xác (đo trên STL: gờ cao 10,0 mm, dày 6,0 mm, cách hình bao 1,0 mm). Bước bào mòn chỉ đẩy vào trong. `simplify` có thể dời một mặt tối đa 0,05 mm, nên phần STL cuối nằm ngoài hình danh nghĩa (cùng quy trình nhưng không bào mòn) tổng cộng dưới 0,4 mm³ mỗi chi tiết (số đo trong `verification.json`). Mọi mặt lắp ghép đều được cắt hoặc ghép chính xác sau bước đó, nên khe hở thiết kế vẫn đúng. Chạy lại cho ra STL giống hệt từng byte: các mặt phẳng được tam giác hóa lại theo thứ tự cố định, vì phép boolean song song của manifold3d có thể chia tam giác khác nhau giữa các lần chạy.

`printkit cad` dừng lại và giữ nguyên file cũ nếu một kiểm tra hỏng. Tên kiểm tra trong `verification.json` giữ đúng tên của bản gốc:

- Mỗi STL kín, hướng mặt nhất quán, một khối, nằm gọn trong 250³ mm và dưới 60.000 tam giác.
- Ở tư thế lắp, không chi tiết nào cắt vào hình bao máy; gân chỉ chạm đáy máy. Rãnh gió dưới máy, vùng giữa hai bộ, vùng cổng trước và sau đều trống.
- Không có hai chi tiết nào chồng lên nhau. Chân tường (34 × 66 mm) và chân cột (34 × 34 mm) vẫn lọt hốc khi to thêm 0,15 mm mỗi bên; chốt to thêm 0,15 mm mỗi bên vẫn lọt lỗ sọ.
- Xích trượt ra khỏi móc 45 mm mà không chạm tường.
- Hình bao tay cầm không cắt vào chi tiết nào, và tì lên cả mặt ngồi lẫn lưng tựa (hạ 0,5 mm là chạm). Mặt ngồi và lưng tựa cách hình bao 0,02 mm để sai số float32 ở mặt tiếp xúc không bị tính là chồng lấn. Mộng to thêm 0,15 mm vẫn lọt hốc. Bệ không chạm đế, cột, sọ, xích hay máy.
- Lấy tay cầm: nhấc 12 mm theo trục nghiêng rồi kéo ra 90 mm theo pháp tuyến mặt trước, không chạm bệ, ngón tay, sọ, cột hay đế; nếu không nhấc thì gờ chặn giữ lại (`ds4_pulls_out_over_the_fingers`).
- Đứng riêng, trọng tâm tay cầm nằm trong đa giác chân cao su của bệ, cách mép 31,7 mm; bệ cùng tay cầm có góc lật 47,1°.
- Animation lấy 2751 mẫu (mỗi bước không chi tiết nào đi quá 1 mm): không có hai chi tiết nào chồng lên nhau ở bất kỳ mẫu nào.
- Gờ chặn đo trên mặt cắt giữa bệ: cao 10 mm, dày 6 mm, cách hình bao 1 mm, sai lệch dưới 0,001 mm.
- Góc lật của cụm đế và máy: 30,06° khi tính PLA đặc và 2 tay cầm, 23,96° khi bỏ qua hoàn toàn khối lượng giá, tính tới tâm chân cao su; ngưỡng yêu cầu là 20°. Bệ tay cầm không gắn cứng nên không tính vào đa giác đỡ.
- STEP đọc lại được 10 solid hợp lệ. Vị trí mà viewer nhận cho mỗi chi tiết, kể cả 6 bản sao của bộ sau, đặt STL trùng với hình CAD trong sai số 0,001 mm.
- Đỉnh vách kẹp không thấp hơn 54 mm sau khi vỡ; tháp nhọn của tường cao 222,5 mm (sai lệch dưới 1 mm); vết vỡ của tường không thấp hơn z = 80 mm; 5–8 vết mẻ sâu tối đa 5 mm (`broken_edges_within_limits`).

Animation gỡ sọ cùng lúc với nhấc tay cầm, và cột bát giác chỉ nâng 7 mm, vì trục nghiêng của tay cầm đi ngang qua sọ và đầu cột (tay cầm chỉ nhấc thẳng được 26 mm khi sọ còn tại chỗ; đầu cột chỉ loe tới 35 mm để cạnh dưới của tay cầm đã nhấc vẫn lướt qua). Phép kiểm tra animation lấy 2751 mẫu, mỗi bước không chi tiết nào đi quá 1 mm.

Những gì code không kiểm tra được: phần nhô và độ dày thành nhỏ nhất (cần Slice trong Bambu Studio và xem Preview). Mép vỡ của tường cửa sổ thu dần về mép dao dưới 0,8 mm ở đỉnh vết vỡ (tại hai cạnh nghiêng của vết nứt, ví dụ khe 0,3 mm ở đáy một nhát cắt chữ V quanh z = 109 mm); Bambu Studio sẽ bỏ phần mỏng đó, chỉ ảnh hưởng hình dáng, không ảnh hưởng độ bền, tải trọng thực (không có FEA), và độ vừa với máy thật (`physical_fit_tested: false`). Các phép kiểm tra trên không thay cho việc in coupon và lắp thử.
