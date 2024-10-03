import { createApp } from "vue"
import { createPinia } from "pinia"
import App from "./App.vue"
import "uno.css"
import { createI18n } from "vue-i18n"
import { messages } from "./lib/i18n"
import * as timeago from 'timeago.js'

const pinia = createPinia()
const i18n = createI18n({
  legacy: false,
  locale: 'cn',
  fallbackLocale: 'en',
  messages,
})

timeago.register('ja_JP', (_number: number, index: number, _totalSec?: number): [string, string] => {
  // number: the timeago / timein number;
  // index: the index of array below;
  // totalSec: total seconds between date to be formatted and today's date;
  return [
    ['たった今', '今すぐ'],
    ['%s 秒前', '%s 秒後'],
    ['1 分前', '1 分後'],
    ['%s 分前', '%s 分後'],
    ['1 時間前', '1 時間後'],
    ['%s 時間前', '%s 時間後'],
    ['1 日前', '1 日後'],
    ['%s 日前', '%s 日後'],
    ['1 週間前', '1 週間後'],
    ['%s 週間前', '%s 週間後'],
    ['1 ヶ月前', '1 ヶ月後'],
    ['%s ヶ月前', '%s ヶ月後'],
    ['1 年前', '1 年後'],
    ['%s 年前', '%s 年後']
  ][index] as [string, string];
})

createApp(App).use(i18n).use(pinia).mount("#app")
