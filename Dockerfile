FROM python:3.13-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    openjdk-17-jdk \
    android-sdk \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Установка Android SDK tools
ENV ANDROID_HOME=/usr/lib/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools

WORKDIR /workspace

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Установка allure для отчётов (опционально)
RUN wget https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz && \
    tar -zxvf allure-2.24.1.tgz -C /opt/ && \
    ln -s /opt/allure-2.24.1/bin/allure /usr/bin/allure && \
    rm allure-2.24.1.tgz

CMD ["pytest", "tests/", "-v"]