
FROM appium/appium:v2.0.1-p0

USER root

# Установка базовых пакетов
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    unzip \
    wget \
    xvfb \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Аргументы сборки для определения платформы
ARG PLATFORM=android
ARG ENABLE_ANDROID=true
ARG ENABLE_IOS=false

# Переменные окружения
ENV PLATFORM=${PLATFORM}
ENV ENABLE_ANDROID=${ENABLE_ANDROID}
ENV ENABLE_IOS=${ENABLE_IOS}

# Установка Android SDK и эмулятора (только если нужен Android)
RUN if [ "$ENABLE_ANDROID" = "true" ]; then \
    # Android SDK уже установлен в базовом образе, добавляем дополнительные компоненты \
    apt-get update && apt-get install -y \
        qemu-kvm \
        libvirt-daemon-system \
        libvirt-clients \
        bridge-utils \
    && rm -rf /var/lib/apt/lists/* \
    # Устанавливаем системные образы Android\
    && yes | sdkmanager --licenses \
    && sdkmanager \
        "system-images;android-30;google_apis;x86_64" \
        "system-images;android-29;google_apis;x86_64" \
        "system-images;android-31;google_apis;x86_64" \
        "platforms;android-30" \
        "platforms;android-29" \
        "platforms;android-31" \
        "build-tools;30.0.3" \
        "emulator" \
        "platform-tools"; \
    fi

# Установка iOS компонентов (только если нужен iOS и мы на macOS)
RUN if [ "$ENABLE_IOS" = "true" ]; then \
    npm install -g \
        appium-xcuitest-driver \
        appium-ios-simulator \
        ios-deploy; \
    fi

# Python окружение
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование зависимостей и установка
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование скриптов
COPY scripts/ ./scripts/
RUN chmod +x scripts/*.sh

# Копирование проекта
COPY . .

# Универсальный скрипт запуска
COPY scripts/universal_setup.sh /usr/local/bin/setup.sh
RUN chmod +x /usr/local/bin/setup.sh

# Порты (будут использоваться в зависимости от платформы)
EXPOSE 4723 4724 5037 5554 5555

# Entrypoint будет определять что запускать на основе переменных окружения
CMD ["/usr/local/bin/setup.sh"]