import cv2
import numpy as np
from PIL import Image

# Загружаем маску и исходное изображение
mask = cv2.imread('birefnet-general.jpg', cv2.IMREAD_GRAYSCALE)
original = cv2.imread('6.jpg')

# Бинаризация маски (пороговое значение)
_, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

# Применяем морфологические операции для очистки маски от дефектов
kernel = np.ones((5, 5), np.uint8)
# Закрытие (убирает выбоины)
binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
# Открытие (убирает наросты)
binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=2)

# Находим контуры
contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Находим самый большой контур по площади
if not contours:
    print("Контуры не найдены!")
    exit(1)

largest_contour = max(contours, key=cv2.contourArea)

# Аппроксимируем контур многоугольником
# Используем итеративный подход для поиска четырёхугольника
epsilon_factor = 0.02
quadrilateral = None

for factor in np.arange(0.02, 0.15, 0.005):
    epsilon = factor * cv2.arcLength(largest_contour, True)
    approx = cv2.approxPolyDP(largest_contour, epsilon, True)
    
    if len(approx) == 4:
        quadrilateral = approx
        break
    elif len(approx) < 4 and quadrilateral is None:
        # Если еще не нашли 4 вершины, сохраняем лучший результат
        quadrilateral = approx

# Если не удалось найти ровно 4 вершины, используем минимальный охватывающий прямоугольник
if quadrilateral is None or len(quadrilateral) != 4:
    # Используем минимальный повёрнутый прямоугольник
    rect = cv2.minAreaRect(largest_contour)
    box = cv2.boxPoints(rect)
    quadrilateral = np.int0(box).reshape(-1, 1, 2)

# Рисуем на исходном изображении
result = original.copy()

# Рисуем зелёные рёбра (линии между вершинами)
for i in range(4):
    pt1 = tuple(quadrilateral[i][0])
    pt2 = tuple(quadrilateral[(i + 1) % 4][0])
    cv2.line(result, pt1, pt2, (0, 255, 0), 3)

# Рисуем красные кружки (вершины)
for point in quadrilateral:
    center = tuple(point[0])
    cv2.circle(result, center, 10, (0, 0, 255), -1)

# Сохраняем результат
cv2.imwrite('out.jpg', result)

print("Готово! Результат сохранён в out.jpg")
print(f"Найдено вершин: {len(quadrilateral)}")

# ============================================================================
# Перспективное преобразование: вырезаем четырёхугольник и превращаем в прямоугольник
# ============================================================================

# Получаем координаты вершин четырёхугольника
pts = quadrilateral.reshape(4, 2).astype(np.float32)

# Вычисляем расстояния между вершинами для определения ширины и высоты
def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

# Упорядочиваем точки: top-left, top-right, bottom-right, bottom-left
# Сначала сортируем по сумме координат (x+y)
rect = np.zeros((4, 2), dtype=np.float32)
s = pts.sum(axis=1)
rect[0] = pts[np.argmin(s)]  # top-left (наименьшая сумма)
rect[2] = pts[np.argmax(s)]  # bottom-right (наибольшая сумма)

# Оставшиеся две точки сортируем по разности (y-x)
diff = np.diff(pts, axis=1)
rect[1] = pts[np.argmin(diff)]  # top-right (наименьшая разность)
rect[3] = pts[np.argmax(diff)]  # bottom-left (наибольшая разность)

# Вычисляем ширину и высоту выходного прямоугольника
width_top = distance(rect[0], rect[1])
width_bottom = distance(rect[2], rect[3])
width = int(max(width_top, width_bottom))

height_left = distance(rect[0], rect[3])
height_right = distance(rect[1], rect[2])
height = int(max(height_left, height_right))

# Определяем ориентацию и создаём целевой прямоугольник
# Если высота больше ширины, то портретная ориентация
if height > width:
    # Портретная ориентация - меняем местами width и height
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    final_width, final_height = width, height
else:
    # Ландшафтная ориентация
    dst = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    final_width, final_height = width, height

# Вычисляем матрицу перспективного преобразования
M = cv2.getPerspectiveTransform(rect, dst)

# Применяем перспективное преобразование
warped = cv2.warpPerspective(original, M, (final_width, final_height))

# Сохраняем результат
cv2.imwrite('cover.jpg', warped)

print("Обложка сохранена в cover.jpg")
print(f"Размер обложки: {final_width}x{final_height} пикселей")
