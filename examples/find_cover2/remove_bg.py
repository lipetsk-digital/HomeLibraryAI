from rembg import new_session, remove
from PIL import Image
import numpy as np

# Открываем изображение
input_image = Image.open('1.jpg')

# Удаляем фон+
model_name = "birefnet-cod"
session = new_session(model_name)
output_image = remove(input_image, only_mask=True)

# Делаем края более чёткими - убираем полупрозрачность
data = np.array(output_image)
if output_image.mode == 'RGBA':
    # Получаем альфа-канал
    alpha = data[:, :, 3]
    # Применяем пороговое значение: если прозрачность > 32, делаем полностью непрозрачным
    alpha = np.where(alpha > 32, 255, 0)
    data[:, :, 3] = alpha
    # Заменяем цвет прозрачных пикселей на белый (чтобы не было чёрного)
    mask = alpha == 0
    data[mask, 0:3] = [255, 255, 255]  # Только RGB, альфа уже 0
    output_image = Image.fromarray(data)

# Конвертируем RGBA в RGB с белым фоном для сохранения в JPEG
if output_image.mode == 'RGBA':
    # Создаем белый фон
    rgb_image = Image.new('RGB', output_image.size, (255, 255, 255))
    # Накладываем изображение с прозрачностью на белый фон
    rgb_image.paste(output_image, mask=output_image.split()[3])
    output_image = rgb_image

# Сохраняем результат
output_image.save('out.jpg')

print("Фон успешно удален! Результат сохранен в out.jpg")
