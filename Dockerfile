FROM python:3.11-slim

# تثبيت الاعتماديات الحديثة الأساسية فقط وتنزيل متصفح كروم المستقر
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    && curl -fsSL https://google.com | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64] http://google.com stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت مكتبات بايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات المشروع
COPY . .

# أمر التشغيل المباشر الآمن
CMD ["python", "main.py", "-a", "accounts.txt", "-l", "links.txt", "--headless", "--no-sandbox", "--verbose"]
