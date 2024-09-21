import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';

// Initialize i18n
i18n
  .use(Backend) // load translation using http backend
  .use(LanguageDetector) // detect user language
  .use(initReactI18next) // pass the i18n instance to react-i18next
  .init({
    fallbackLng: 'en', // default language if language is not detected
    debug: true, // enable debug to see console output for language switching issues

    backend: {
      loadPath: '/locales/{{lng}}/translation.json', // Path to load the translation files
    },

    interpolation: {
      escapeValue: false, // React already escapes values, so no need to escape
    }
  });

export default i18n;
