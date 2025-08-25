# Инструкции по настройке бота в Render

## Переменные окружения в Render Dashboard

После создания сервиса в Render, необходимо настроить следующие переменные окружения в Dashboard:

### Обязательные переменные:

1. **TELEGRAM_BOT_TOKEN**
   - Значение: токен вашего Telegram бота от @BotFather
   - Пример: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **OPENAI_API_KEY**
   - Значение: ваш API ключ от OpenAI
   - Пример: `sk-proj-...`

### Настройки уже включены в render.yaml:

- `PYTHON_VERSION: 3.11`
- `OPENAI_MODEL: gpt-4o-mini`
- `OPENAI_MAX_TOKENS: 2000`
- `OPENAI_TEMPERATURE: 0.3`
- `SERVER_HOST: 0.0.0.0`
- `PORT: 8000`
- `WEBHOOK_URL: https://umbb-gpt-bot.onrender.com/webhook`
- `TESSERACT_CMD: /usr/bin/tesseract`
- `OCR_LANGUAGES: eng,rus,deu,fra,spa,ita,por,chi_sim,jpn,kor`
- `OCR_ENGINE: tesseract`
- `TRANSLATION_SERVICE: openai`
- `MAX_IMAGE_SIZE: 10485760`
- `SUPPORTED_IMAGE_FORMATS: jpg,jpeg,png,bmp,tiff,webp`

## Шаги развертывания:

1. **Подключите GitHub репозиторий** к Render
2. **Выберите бесплатный план** (Free)
3. **Установите переменные окружения** в разделе Environment
4. **Дождитесь автоматического деплоя** после push в main ветку

## Проверка работы:

- Проверьте логи деплоя в Render Dashboard
- Убедитесь, что сервис запустился без ошибок
- Протестируйте бота в Telegram

## Возможные проблемы:

1. **Ошибки установки зависимостей**: проверьте requirements.txt
2. **Таймаут деплоя**: увеличьте время в render.yaml (уже настроено)
3. **Ошибки Tesseract**: проверьте preDeployCommand в логах

## Мониторинг:

- Используйте `/health` endpoint для проверки статуса
- Логи доступны в Render Dashboard
- Автоматический перезапуск при падении сервиса