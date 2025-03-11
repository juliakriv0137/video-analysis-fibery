# Настройка интеграции с Fibery для анализа видео

## Требования
- Аккаунт Fibery
- Репозиторий GitHub с кодом системы анализа
- API ключи и токены:
  - OpenAI API key
  - GitHub токен с правами на workflow
  - Fibery API токен

## Шаг 1: Настройка GitHub

1. Откройте настройки репозитория:
   - Перейдите в `Settings` -> `Secrets and variables` -> `Actions`
   - Добавьте следующие секреты:
     ```
     OPENAI_API_KEY=ваш_ключ_openai
     FIBERY_API_TOKEN=ваш_токен_fibery
     FIBERY_WORKSPACE=имя_вашего_workspace
     GITHUB_TOKEN=ваш_токен_github
     ```

## Шаг 2: Создание типа в Fibery

1. Войдите в Fibery
2. Перейдите в `Settings` -> `Types & Fields`
3. Создайте новый тип:
   - Name: `Video`
   - Icon: 🎥
   - Collection Name: `Videos`

4. Добавьте поля:
   - Поле для URL:
     ```
     Name: Video URL
     Type: Text
     Required: Yes
     ```
   - Поле для результатов:
     ```
     Name: Analysis Results
     Type: Text (Long)
     Rich Text: Yes
     ```

## Шаг 3: Создание кнопки анализа

1. В настройках типа `Video`:
   - Перейдите в `Buttons`
   - Нажмите `+ Add Button`
   - Укажите:
     ```
     Name: Analyze Video
     Icon: 🔍
     Color: Blue
     ```

## Шаг 4: Настройка автоматизации

1. Откройте `Automations`
2. Создайте новую автоматизацию:
   ```
   Trigger:
   - Type: Button Click
   - Button: Analyze Video
   - Entity Type: Video

   Action:
   - Type: Call Webhook
   - URL: https://[ваш-домен]/webhook/fibery
   - Method: POST
   - Headers:
     Content-Type: application/json
   
   Body:
   {
     "action": {
       "type": "Button Click"
     },
     "entity": {
       "fibery/id": "${fibery/id}",
       "Video URL": "${Video URL}"
     }
   }
   ```

## Шаг 5: Тестирование

1. Создайте тестовую запись:
   - Тип: Video
   - Заполните поле Video URL
   - Нажмите кнопку Analyze Video

2. Проверьте:
   - Запуск GitHub Actions workflow
   - Появление результатов в поле Analysis Results
   - Логи в Actions

## Troubleshooting

### Ошибка "No video URL found"
- Проверьте, что поле Video URL заполнено
- Убедитесь, что имя поля в автоматизации совпадает с реальным

### Ошибка "Workflow failed"
- Проверьте секреты в GitHub
- Посмотрите логи в Actions
- Убедитесь, что URL видео доступен

### Ошибка "Token invalid"
- Обновите токены в GitHub Secrets
- Проверьте права доступа токенов

## Структура ответа от системы

Успешный анализ возвращает:
```json
{
  "status": "success",
  "message": "Analysis completed",
  "details": {
    "summary": "Общее описание видео",
    "frames": [
      {
        "timestamp": "00:00",
        "description": "Описание кадра",
        "detected_text": "Распознанный текст"
      }
    ],
    "audio": {
      "transcription": "Текст из аудио",
      "music_detected": true/false
    }
  }
}
```

## Поддержка

При возникновении проблем:
1. Проверьте логи в GitHub Actions
2. Убедитесь, что все токены актуальны
3. Проверьте настройки автоматизации в Fibery
