import { createApp } from "vue"
import { createPinia } from "pinia"
import App from "./App.vue"
import "uno.css"
import { createI18n } from "vue-i18n"
import { messages } from "./lib/i18n"

const pinia = createPinia()
const i18n = createI18n({
  legacy: false,
  locale: 'cn',
  fallbackLocale: 'en',
  messages,
})
createApp(App).use(i18n).use(pinia).mount("#app")
