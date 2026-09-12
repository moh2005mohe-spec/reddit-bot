FROM python:3.11-slim

# تثبيت متصفح كروم المستقر والاعتماديات الرسومية مباشرة بدون تعقيدات روابط مستودعات خارجية
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    && wget -q https://google.com \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت المكتبات الأساسية
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات الحسابات والروابط
COPY . .

# أمر التشغيل المباشر للبوت في الوضع المخفي والآمن
CMD ["python", "main.py", "-a", "accounts.txt", "-l", "links.txt", "--headless", "--no-sandbox", "--verbose"]
