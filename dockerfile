FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
ADD https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx /root/.u2net/birefnet-general.onnx
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "homelib.py"]