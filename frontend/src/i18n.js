import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

const resources = {
  uk: {
    translation: {
      "Narrative Drift Radar": "Радар Зміни Наративів",
      "Tracking narrative shifts in real-time": "Відстеження змін наративів у реальному часі",
      "Narrative Timeline": "Хронологія Наративів",
      "Active Narratives": "Активні Наративи",
      "Loading narrative data...": "Завантаження даних наративів...",
      "Error": "Помилка",
      "Failed to fetch timeline data. Make sure the backend is running.": "Не вдалося завантажити дані хронології. Переконайтеся, що бекенд запущено.",
      "total events": "всього подій",
      "No active narratives found.": "Активні наративи не знайдено.",
      "Load More": "Завантажити ще",
      "Loading more...": "Завантаження...",
      "Show More": "Показати більше",
      "Show Less": "Показати менше",
      "Narrative Emergence": "Виникнення Наративу",
      "Narrative Shift": "Зміна Наративу", 
      "Narrative Peak": "Пік Наративу",
      "Narrative Decline": "Занепад Наративу",
      "Event": "Подія",
      "Score": "Оцінка",
      "Diversity": "Різноманітність",
      "Sources": "Джерела",
      "Coherence": "Узгодженість", 
      "Support": "Підтримка",
      "related articles": "пов'язаних статей",
      "from": "з",
      "sources": "джерел",
      "...and": "...та ще",
      "more articles": "статей більше",
      "Showing": "Показано",
      "of": "з",
      "events": "подій",
      "Page": "Сторінка",
      "Loading...": "Завантаження...",
      "Load More Events": "Завантажити ще події",
      "No timeline events available yet.": "Події хронології поки що недоступні.",
      "Run the data processing commands to generate narrative events.": "Запустіть команди обробки даних для генерації подій наративу."
    }
  },
  en: {
    translation: {
      "Narrative Drift Radar": "Narrative Drift Radar",
      "Tracking narrative shifts in real-time": "Tracking narrative shifts in real-time",
      "Narrative Timeline": "Narrative Timeline",
      "Active Narratives": "Active Narratives",
      "Loading narrative data...": "Loading narrative data...",
      "Error": "Error",
      "Failed to fetch timeline data. Make sure the backend is running.": "Failed to fetch timeline data. Make sure the backend is running.",
      "total events": "total events",
      "No active narratives found.": "No active narratives found.",
      "Load More": "Load More",
      "Loading more...": "Loading more...",
      "Show More": "Show More",
      "Show Less": "Show Less",
      "Narrative Emergence": "Narrative Emergence",
      "Narrative Shift": "Narrative Shift",
      "Narrative Peak": "Narrative Peak", 
      "Narrative Decline": "Narrative Decline",
      "Event": "Event",
      "Score": "Score",
      "Diversity": "Diversity",
      "Sources": "Sources",
      "Coherence": "Coherence",
      "Support": "Support",
      "related articles": "related articles",
      "from": "from",
      "sources": "sources",
      "...and": "...and",
      "more articles": "more articles",
      "Showing": "Showing",
      "of": "of",
      "events": "events",
      "Page": "Page",
      "Loading...": "Loading...",
      "Load More Events": "Load More Events",
      "No timeline events available yet.": "No timeline events available yet.",
      "Run the data processing commands to generate narrative events.": "Run the data processing commands to generate narrative events."
    }
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'uk',
    lng: 'uk',
    debug: true,

    interpolation: {
      escapeValue: false,
    },
    
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage']
    }
  })

export default i18n
