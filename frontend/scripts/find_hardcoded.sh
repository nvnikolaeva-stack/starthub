#!/bin/bash
# Ищет захардкоженные русские строки в компонентах (не в файлах переводов)
# Запуск: cd frontend && bash scripts/find_hardcoded.sh

echo "🔍 Поиск захардкоженных русских строк в компонентах..."
echo ""

WORDS=("Календарь" "Ближайшие" "Добавить" "Статистика" "Плавание" "Бег" "Велогонка" "Триатлон" "Прочее" "Участник" "Сохранить" "Отмена" "Удалить" "Редактировать" "Подробнее" "Локация" "Дистанция" "Заметки")

FOUND=0
for word in "${WORDS[@]}"; do
    RESULTS=$(grep -rn "$word" src/components/ src/app/ --include="*.tsx" --include="*.ts" \
        | grep -v "messages/" \
        | grep -v "__tests__/" \
        | grep -v "node_modules/" \
        | grep -v "// " \
        | grep -v "console.log")

    if [ -n "$RESULTS" ]; then
        echo "⚠️  «$word» найдено:"
        echo "$RESULTS" | head -5
        echo ""
        FOUND=$((FOUND + 1))
    fi
done

if [ $FOUND -eq 0 ]; then
    echo "✅ Захардкоженных русских строк не найдено!"
else
    echo "❌ Найдено $FOUND слов. Замени их на вызовы useTranslations()."
fi
