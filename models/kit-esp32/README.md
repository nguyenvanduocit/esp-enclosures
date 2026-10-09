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
- Hai hàng chân header hàn xuống, nằm ngoài các trụ (cách mép trụ 1,2 mm theo trục x) và dài 8,5 mm dưới PCB, còn cách sàn 6,1 mm.
- Khe USB-C rộng 12 mm, cao 6 mm, thừa hơn đầu cắm 9 × 3,2 mm của bo; ốp lưng cáp quá to có thể không vừa.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Hướng mặt: cổng USB-C quay ra mặt −y, đối diện nắp (+y). Khe USB-C nằm trong dải giữa hai hàng lỗ khoét của mặt đó.
- Đặt bo lên bốn trụ, mặt linh kiện hướng lên, USB-C sát khe. Cố định bo bằng keo hoặc băng dính hai mặt vì trụ chỉ đỡ mặt dưới PCB.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +y. Nắp có gờ lồng vào thân, không cần vít.
- In: thân mở lên (mặt +y hướng lên), nắp úp mặt ngoài xuống bàn in. Slicer cảnh báo nắp: đặt `print_rotation` (-90, 0, 90) giảm vùng nhô từ 426,5 mm² xuống 316,5 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
