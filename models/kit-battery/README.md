# Module pin 18650 + sạc

Mở trong [app chung](../../#model/kit-battery). Khối 3×4×2 đơn vị (59,8 × 79,8 × 39,8 mm), nắp ở mặt +x.

## Cần mua
| Linh kiện | Số lượng | Ghi chú |
|---|---|---|
| Khay pin 18650 đơn, loại hở | 1 | 75 × 22 × 18 mm theo trang bán hàng |
| Mạch sạc TP4056 USB-C có mạch bảo vệ | 1 | 26 đến 29 × 17 × 4,1 đến 4,9 mm theo trang bán hàng; mô hình dùng 28 × 17 × 4,9 |
| Pin 18650 | 1 | Mô hình dùng Ø18,5 × 65,3 mm |
| Nam châm tròn 5×1,5 | 4 mỗi mối ghép (lắp kín: 104) | Shopee có bộ 10 viên 5×1,5 |
| Vòng đệm thép mạ kẽm M6 DIN 125 (12×6,4×1,6) | 1 mỗi mối ghép (lắp kín: 26) | Không dùng inox |

## Giả định
- Kích thước khay và mạch sạc từ trang bán hàng; đo linh kiện của bạn trước khi in.
- Chiều dài trong của thân là 75,8 mm cho khay 75 mm: chỉ còn 0,8 mm cho cả hai đầu (0,4 mm mỗi đầu). Khay dài hơn sẽ không vừa.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.
- Khe USB-C rộng 10,4 mm, cao 4,6 mm, thừa hơn đầu cắm 9 × 3,3 mm của mạch; ốp lưng cáp quá to có thể không vừa.
- Không có mạch tăng áp. Bạn tự chọn cách nối pin với ESP32-C3 SuperMini.
- Mạch sạc được giữ bằng hai gờ chặn trước và một móc gài, yếu hơn cách giữ bằng hai móc của các module khác: chỉ một móc nhún được. Lực giữ chưa đo; in thân, gài mạch thật và thử trước khi in cả bộ. Gờ và ngạnh cách mép PCB 0,1 mm, đè lên mặt PCB 0,8 mm và cách mặt PCB 0,2 mm. Bộ kiểm tra chứng minh mạch dài 27,7 đến 28,3 mm (theo trục y) và rộng 16,7 đến 17,3 mm, tức mô hình 28 × 17 mm ±0,3 mm. Trong khoảng đó, dù mạch dồn về phía nào, gờ và ngạnh vẫn đè ít nhất 0,4 mm; mạch dài hơn 28,2 mm đẩy móc ra (chân móc giãn 0,79 % khi gài). Mạch ngoài khoảng này chưa được kiểm; trang bán hàng ghi 26 đến 29 mm, nên mạch 26 mm không được giữ. Trước khi in, đo chiều dài mạch. PCB dày quá 1,8 mm thì không lọt dưới gờ. Ngạnh và gờ nằm trên dải 0,8 mm sát hai cạnh ngắn của mạch: dải đó phải trống, không có linh kiện hay mối hàn nhô quá 0,2 mm.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Khay pin dán lên sàn, sát mặt −x (cách thành 0,8 mm để chừa chỗ cho keo; mô hình đặt đáy khay cách sàn 0,8 mm, lớp keo lấp khoảng đó); pin nằm dọc theo trục y.
- Mạch sạc đặt trên bốn trụ cao 14,65 mm so với sàn, mặt linh kiện hướng lên. Cổng USB-C quay ra khe ở mặt −y, nằm trong dải giữa hai hàng lỗ khoét của mặt đó.
- Điểm chặn trước là hai gờ cứng trên mặt trong tường −y, mỗi gờ rộng 3,1 mm, ở hai bên khe USB-C (cách khe 0,2 mm). Đầu cổng USB-C nằm cách mặt trong tường 0,6 mm nên chính khe không chặn được mạch nhấc lên. Gờ cũng che mép −y của PCB nên mạch không trượt về phía tường được quá 0,1 mm.
- Một móc gài mọc từ sàn ở cạnh +y, rộng 4 mm, dày 1,2 mm, chân bo tròn 0,6 mm cả hai mặt, lệch 2,2 mm về phía +x so với giữa cạnh để chân móc không đứng trên lỗ vòng đệm ở sàn.
- Theo y, gờ chặn và móc giữ mạch xê dịch 0,1 mm mỗi phía; theo x, cổng USB-C chạm hai gờ chặn sau 0,9 mm mỗi phía (0,98 mm với mạch nhỏ hơn 0,3 mm).
- Gài mạch: nghiêng mạch, luồn cạnh có cổng USB-C vào dưới hai gờ chặn, rồi ấn đầu +y xuống bốn trụ. Mép mạch đẩy mặt vát của ngạnh ra ngoài và móc bật lại. Không cần keo. Tháo mạch: gạt đỉnh móc về phía +y khoảng 0,6 mm, nhấc đầu +y lên rồi rút mạch ra khỏi gờ.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +x. Nắp có gờ lồng vào thân, không cần vít. Thay pin bằng cách mở nắp này.
- In: thân mở lên (mặt +x hướng lên, cao 57,8 mm), nắp úp mặt ngoài xuống bàn in. Thân có vùng nhô 1976,0 mm², tăng 32,2 mm² so với thân không móc. Móc in nằm ngang nên mặt dưới thân móc, kể cả hai góc bo ở chân, là một cầu 2,7 × 17,75 mm (22,2 mm²) ở độ cao 36,1 mm. Đầu dưới mỗi gờ chặn là một cầu 2,2 × 3,0 mm (5,0 mm²), ở độ cao 27,4 mm và 41,3 mm. Thử in một thân trước khi in cả bộ. Slicer cảnh báo nắp: vùng nhô 804,9 mm² khi úp mặt ngoài xuống bàn; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 442,0 mm² nhưng chỉ chạm bàn 40,1 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
