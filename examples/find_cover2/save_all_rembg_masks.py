from rembg import remove, new_session, session_factory
from PIL import Image
import numpy as np
import time

# Список моделей rembg (актуально на 2025 год)
ALL_MODELS = [
    'u2net',
    'u2netp',
    'u2net_human_seg',
    'u2net_cloth_seg',
    'silueta',
    'isnet-general-use',
    'isnet-anime',
    'sam',
    'birefnet-general',
    'birefnet-general-lite',
    'birefnet-portrait',
    'birefnet-dis',
    'birefnet-hrsod',
    'birefnet-cod',
    'birefnet-massive'
]

input_image = Image.open('4.jpg')

for model_name in ALL_MODELS:
    start_time = time.time()
    session = new_session(model_name)
    mask = remove(input_image, session=session, only_mask=True)
    # Преобразуем маску к чёрно-белому виду (0/255)
    mask_np = np.array(mask)
    if mask.mode == 'RGBA':
        # Берём только альфа-канал
        mask_bw = mask_np[:, :, 3]
    else:
        mask_bw = mask_np
    # Порог
    mask_bw = np.where(mask_bw > 1, 255, 0).astype(np.uint8)
    mask_img = Image.fromarray(mask_bw, mode='L')
    mask_img.save(f'{model_name}.jpg')
    elapsed = time.time() - start_time
    print(f"Model: {model_name}, Time: {elapsed:.2f} seconds")
print("Done!")
