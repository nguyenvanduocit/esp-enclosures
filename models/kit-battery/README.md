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
- Chiều dài trong của thân là 75,8 mm cho khay 75 mm: chỉ còn 0,4 mm. Khay dài hơn sẽ không vừa.
- Lực hút nam châm chưa đo: in một mối ghép và kéo thử trước khi in cả bộ.
- Khe USB-C rộng 10,4 mm, cao 4,6 mm, thừa hơn đầu cắm 9 × 3,3 mm của mạch; ốp lưng cáp quá to có thể không vừa.
- Không có mạch tăng áp. Bạn tự chọn cách nối pin với ESP32-C3 SuperMini.

## Lắp
- Thứ tự dán: dán nam châm vào lỗ ở ba mặt dương (+x, +y, +z) và vòng đệm vào lỗ ở ba mặt âm (−x, −y, −z) bằng keo, đủ số cần cho từng mối ghép. Phía sau chúng chỉ còn sàn mỏng nên không dán thì bị hút ra.
- Khay pin dán vào sàn, sát mặt −x (cách thành 0,8 mm để chừa chỗ cho keo); pin nằm dọc theo trục y.
- Mạch sạc đặt trên bốn trụ cao 14,65 mm so với sàn, mặt linh kiện hướng lên. Cổng USB-C quay ra khe ở mặt −y, nằm trong dải giữa hai hàng lỗ khoét của mặt đó. Cố định mạch bằng keo hoặc băng dính hai mặt vì trụ chỉ đỡ mặt dưới PCB.
- Luồn dây qua cổng Ø5 ở giữa mỗi đơn vị trên các mặt, rồi đóng nắp +x. Nắp có gờ lồng vào thân, không cần vít. Thay pin bằng cách mở nắp này.
- In: thân mở lên (mặt +x hướng lên, cao 57,8 mm), nắp úp mặt ngoài xuống bàn in. Slicer cảnh báo nắp: vùng nhô 804,9 mm² khi úp mặt ngoài xuống bàn; hướng slicer gợi ý (đặt nắp đứng trên cạnh) còn 442,0 mm² nhưng chỉ chạm bàn 40,1 mm².

## File
`shell.stl`, `lid.stl` (in), `assembly.step`, `model.json`, `verification.json`: sinh ra, không sửa tay.
