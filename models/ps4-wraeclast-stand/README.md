# PS4 · Phế tích Wraeclast

Giá dựng đứng cho PS4 đời đầu (CUH-1000A), trang trí như một góc phế tích: cột đá khắc rune, cột gãy đội sọ, xích sắt gãy mắt cuối, và hai bệ đá đỡ tay cầm DualShock 4. Máy đứng trên mặt hông hẹp, kẹp giữa hai cụm đế giống hệt nhau đặt ở nửa trước và nửa sau máy; mỗi cụm có một bệ tay cầm đứng sát bên. Rune, sọ, xích, vết vỡ và vết bào mòn đều sinh bằng code trong `model.py`, dùng các hàm thuần trong `printkit/art.py`. Không dùng mesh, logo hay chữ lấy từ game.

Mở model trong [app chung](../../#model/ps4-wraeclast-stand); bản ZIP có `index.html` chạy offline. Chế độ **Tháo lắp** gỡ sọ, xích và nhấc tay cầm ra cùng lúc, trượt bệ tay cầm ra ngoài, nhấc máy, nâng cột khỏi hốc, rồi lắp lại theo thứ tự ngược. Sidebar có **Hiển thị** để ẩn từng chi tiết (ẩn PS4 thì số đo chiều cao đổi sang chiều cao giá), **Đo** để bật kích thước, **In & tải** để lấy file và cấu hình in.

## In coupon trước

`fitCoupon.stl` là một lát của đế: một gân đỡ, hai vách kẹp và rãnh gió, nặng khoảng 22 g. In nó trước rồi đặt thử lên máy thật. Máy phải lọt khe 54 mm, nằm êm trên gân và không chạm đáy rãnh gió. Chỉ in hai đế (≈ 110 g/cái) khi coupon đã vừa. Nếu quá chặt hoặc quá lỏng, chỉnh bù biên XY hoặc flow của máy in; không scale STL vì sẽ làm sai hốc cột và chốt sọ.

## Kéo từng chi tiết

Rê chuột lên chi tiết để làm sáng nó và hiện mũi tên, rồi kéo theo mũi tên. Đế đi xuống; cột cao, cột gãy, sọ và PS4 đi lên; xích trượt ra khỏi móc theo phương ngang; bệ tay cầm trượt ra xa máy; tay cầm đi lên theo trục nghiêng 70°. Đây là thao tác minh họa, không mô phỏng va chạm khi kéo: kéo tay cầm quá 19 mm khi sọ còn tại chỗ thì hình tay cầm đi xuyên qua sọ.

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

- **Đế** 170 × 80 mm, hai bậc cao 10 mm. Hai vách kẹp cao tới 65 mm; đỉnh vỡ thấp nhất đo được 56,7 mm. Khe giữa rộng 54 mm (máy 53 mm, hở 0,5 mm mỗi bên) cắt suốt chiều sâu xuống còn sàn 6 mm, tạo rãnh gió cao 14 mm dưới máy. Hai gân rộng 8 mm đỡ máy ở cao độ 20 mm. Hai hốc cột 34,4 × 34,4 × 6 mm. Mặt dưới có 4 hõm Ø12 × 1,5 mm cho chân cao su. Mặt trước bậc dưới khắc một dải rune.
- **Cột cao** tiết diện 34 × 34 mm vát cạnh 4 mm, cao 210 mm tính từ đáy hốc (đỉnh vỡ cao nhất 207,5 mm, tức z ≈ 221,5 mm). Đỉnh vỡ có các nhát cắt nằm trong 30 mm trên cùng; 5–8 vết mẻ dọc cạnh, sâu tối đa 6 mm. Hai mặt +X và −Y khắc mỗi mặt một cột 6 rune (18 × 18 mm, nét 2 mm, sâu 1,5 mm). Móc treo xích Ø6 × 20 mm có gân 45° bên dưới.
- **Cột gãy** cùng tiết diện, cao 100 mm, mặt ngồi phẳng tuyệt đối ở z = 100 mm. Các vết mẻ chỉ làm thấp mép, không bao giờ nhô lên trên mặt ngồi. Chốt Ø8 × 6 mm giữ sọ.
- **Sọ** không hàm khoảng 41 × 53 × 46,5 mm, nhìn ra ngoài. Có gờ mày, hốc mắt sâu, lỗ mũi, gò má, cung gò má và hàng răng trên. Đáy phẳng có lỗ Ø8,4 × 7 mm cắm vào chốt.
- **Xích** 7 mắt, dây Ø4 mm, lòng mắt rộng 8 mm (móc Ø6 hở 1 mm mỗi bên). Các mắt chồng nhau 0,4 mm nên cả xích in thành một khối. Mắt cuối có khe gãy 2 mm.

- **Bệ tay cầm** 94 × 182 mm, đặt ở phía cột gãy (−X), sát đầu đế. Tay cầm nghiêng 70° so với mặt bàn, mặt hướng ra ngoài, đầu có cổng micro-USB hướng về đế. Đáy tay cầm tì lên mặt ngồi nghiêng 20° (khối đặc bên dưới); lưng tựa dày 8 mm chỉ cao 60% chiều dài tay cầm nên cổng sạc vẫn thông. Gờ chặn cao 10 mm, hở 1 mm trước tay cầm; hai má là trụ gãy dày 8 mm, hở 2 mm, đỉnh vỡ cao tối đa 60 mm. Mặt ngoài bậc đáy khắc dải rune; mặt dưới có 4 hõm chân cao su. Mộng 39,6 × 19,8 × 5,6 mm ở đầu +X cắm vào hốc dưới đầu −X của đế (hở 0,2 mm). Mộng chỉ định vị: bệ đứng riêng trên chân cao su của nó và tự chịu tải.

Hai bộ dùng chung một bộ STL; bộ sau là bộ trước xoay 180° quanh trục đứng. Hai cụm đế nằm trong y = ±52,5…132,5 mm, không che cổng trước, cổng sau và lỗ thoát nhiệt. Bệ tay cầm chiếm x = ±86…180 mm, cách vùng cổng 1 mm.

**Lấy tay cầm:** nhấc lên khỏi gờ chặn (hơn 10 mm theo trục nghiêng) rồi kéo ra phía ngoài. Nhấc thẳng theo trục nghiêng chỉ đi được 19 mm rồi chạm sọ, vì trục này hướng về phía cột gãy.

## File in và tái tạo

- `fitCoupon.stl`: coupon thử khe, đáy xuống bàn, in đầu tiên.
- `plinth.stl`: đế, in 2 cái, đáy xuống bàn. Hõm chân cao su là cầu Ø12 mm, hốc mộng ở đầu −X là cầu rộng 40 mm; chỉ bật support ở các vùng đó nếu cầu bị võng.
- `pillar.stl`: cột cao, in 2 cái, đứng thẳng. Móc xích in được nhờ gân 45°, không cần support; nên dùng brim 5 mm vì cột cao và mảnh.
- `stub.stl`: cột gãy, in 2 cái, đứng thẳng, không cần support.
- `skull.stl`: sọ, in 2 cái, đáy phẳng xuống bàn. **Cần tree support** cho mái hốc mắt, mặt dưới gò má, hàng răng và phần dưới hộp sọ: `verification.json` đo được 453 mm² mặt dốc hơn 45°.
- `altar.stl`: bệ tay cầm, in 2 cái, đáy xuống bàn, không cần support. Mộng nằm sát bàn nên in được không cần đỡ. Phần nhô còn lại (545 mm²) gần như toàn bộ là trần 4 hõm chân cao su. Xem gờ chặn và rãnh rune trong Preview.
- `chain.stl`: xích, in 2 cái, nằm ngang với các mắt nghiêng ±45°, điểm thấp nhất chạm bàn. **Cần tree support** (868 mm² mặt dốc hơn 45°); gỡ nhẹ tay. `printkit cad` cảnh báo `chain: set print_rotation to (0, 0, -45)` vì xoay như vậy để một nửa số mắt nằm phẳng, overhang giảm còn khoảng 304 mm². Model giữ các mắt nghiêng ±45° có chủ ý: mọi mắt in giống nhau, không mắt nào là vòm đứng 90° cao 16 mm; cảnh báo này đã được xem xét và giữ nguyên.
- `assembly.step`: chỉ chứa phần cơ khí của hai bộ ở vị trí lắp: đế, cột cao, cột gãy, xích, bệ tay cầm, tổng 10 solid, trước khi bào mòn, không có sọ và tay cầm. Đây là file để sửa kích thước. File STEP không giống hệt từng byte giữa các lần chạy (có dấu thời gian), nên sau mỗi lần `printkit cad` cần chạy lại `printkit build` để ZIP khớp với thư mục.
- `model.py`: nguồn duy nhất: CadQuery cho phần cơ khí, SDF của sọ, bảng rune, xích, và toàn bộ `@model.check`. Hàm SDF, bào mòn và lưới chuẩn tắc dùng chung nằm trong `printkit/art.py`.
- `reference/ds4.stl`, `reference/ds4Back.stl`: hộp bao tay cầm nghiêng 20°, chỉ để xem.
- `model.json`, `verification.json`: sinh ra, không sửa tay. `model.json` theo [schema chung](../../model.schema.json).

```sh
uv run printkit cad ps4-wraeclast-stand   # khoảng 1 phút
uv run printkit build
```

Quy trình cho mỗi chi tiết đá như sau. CadQuery dựng phôi, kể cả các nhát cắt vỡ và vết mẻ với seed cố định. `art.erode` chia lưới khoảng 0,8 mm rồi đẩy từng đỉnh **chỉ vào trong**, sâu tối đa 1 mm theo pháp tuyến đã làm mượt. Lớp 1 mm sát mặt bàn và các vùng che (chân cột, mặt khắc rune, mặt trước dải rune) không bị đẩy. Sau bước này là `simplify(0.05)`. Cuối cùng mới cắt các phần chính xác: khe máy, đỉnh gân, hốc cột, hốc mộng, hõm chân cao su, rãnh rune, mặt ngồi cột gãy, mặt ngồi, lưng tựa và gờ chặn của bệ; và ghép các phần chính xác: chân cột 34 mm, móc xích, chốt sọ, mộng bệ. Phôi bệ đắp dư 3 mm vào chỗ tay cầm và lên mặt trên, mặt ngoài của gờ chặn, để nhát cắt cuối tạo ra mặt ngồi, lưng tựa và cả ba mặt của gờ chặn chính xác (đo trên STL: gờ cao 10,0 mm, dày 6,0 mm, cách hình bao 1,0 mm). Bước bào mòn chỉ đẩy vào trong. `simplify` có thể dời một mặt tối đa 0,05 mm, nên phần STL cuối nằm ngoài lõi danh nghĩa tổng cộng dưới 0,06 mm³ mỗi chi tiết (số đo trong `verification.json`). Mọi mặt lắp ghép đều được cắt hoặc ghép chính xác sau bước đó, nên khe hở thiết kế vẫn đúng. Chạy lại cho ra STL giống hệt từng byte: các mặt phẳng được tam giác hóa lại theo thứ tự cố định, vì phép boolean song song của manifold3d có thể chia tam giác khác nhau giữa các lần chạy.

`printkit cad` dừng lại và giữ nguyên file cũ nếu một kiểm tra hỏng. Tên kiểm tra trong `verification.json` giữ đúng tên của bản gốc:

- Mỗi STL kín, hướng mặt nhất quán, một khối, nằm gọn trong 250³ mm và dưới 60.000 tam giác.
- Ở tư thế lắp, không chi tiết nào cắt vào hình bao máy; gân chỉ chạm đáy máy. Rãnh gió dưới máy, vùng giữa hai bộ, vùng cổng trước và sau đều trống.
- Không có hai chi tiết nào chồng lên nhau. Chân cột vẫn lọt hốc khi to thêm 0,15 mm mỗi bên; chốt to thêm 0,15 mm mỗi bên vẫn lọt lỗ sọ.
- Xích trượt ra khỏi móc 45 mm mà không chạm cột.
- Hình bao tay cầm không cắt vào chi tiết nào, và tì lên cả mặt ngồi lẫn lưng tựa (hạ 0,5 mm là chạm). Mặt ngồi và lưng tựa cách hình bao 0,02 mm để sai số float32 ở mặt tiếp xúc không bị tính là chồng lấn. Mộng to thêm 0,15 mm vẫn lọt hốc. Bệ không chạm đế, cột, sọ, xích hay máy.
- Đứng riêng, trọng tâm tay cầm nằm trong đa giác chân cao su của bệ, cách mép 31,7 mm; bệ cùng tay cầm có góc lật 48,6°.
- Animation lấy 2751 mẫu (mỗi bước không chi tiết nào đi quá 1 mm): không có hai chi tiết nào chồng lên nhau ở bất kỳ mẫu nào.
- Gờ chặn đo trên mặt cắt giữa bệ: cao 10 mm, dày 6 mm, cách hình bao 1 mm, sai lệch dưới 0,001 mm.
- Góc lật của cụm đế và máy: 30,07° khi tính PLA đặc và 2 tay cầm, 23,96° khi bỏ qua hoàn toàn khối lượng giá, tính tới tâm chân cao su; ngưỡng yêu cầu là 20°. Bệ tay cầm không gắn cứng nên không tính vào đa giác đỡ.
- STEP đọc lại được 10 solid hợp lệ. Vị trí mà viewer nhận cho mỗi chi tiết, kể cả 6 bản sao của bộ sau, đặt STL trùng với hình CAD trong sai số 0,001 mm.
- Đỉnh vách kẹp không thấp hơn 54 mm sau khi vỡ, đỉnh cột gãy nằm trong 30 mm trên cùng, 5–8 vết mẻ sâu tối đa 6 mm (`broken_edges_within_limits`).

Animation gỡ sọ cùng lúc với nhấc tay cầm, và cột gãy chỉ nâng 7 mm, vì trục nghiêng của tay cầm đi ngang qua sọ và cột gãy (tay cầm chỉ nhấc thẳng được 19 mm khi sọ còn tại chỗ). Phép kiểm tra animation lấy 2751 mẫu, mỗi bước không chi tiết nào đi quá 1 mm.

Những gì code không kiểm tra được: phần nhô và độ dày thành nhỏ nhất (cần Slice trong Bambu Studio và xem Preview), tải trọng thực (không có FEA), và độ vừa với máy thật (`physical_fit_tested: false`). Các phép kiểm tra trên không thay cho việc in coupon và lắp thử.
