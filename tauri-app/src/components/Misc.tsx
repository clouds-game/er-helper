import { defineComponent } from "vue"
import { useI18n } from "vue-i18n"

export const Banner = defineComponent<{
  content?: string,
  level: "warn" | "info" | "error",
}>((props, { slots }) => {
  const style = {
    warn: "bg-yellow-200",
    info: "bg-blue-200",
    error: "bg-red-200",
  }
  return () => <div class={`text-center mb-1 ${style[props.level]}`}>
    { props.content }
    { slots.default && slots.default() }
  </div>
}, {
  name: "Banner",
  props: ['content', 'level'],
})

export const PlayerCard = defineComponent<{
  nickname: string,
  role_name: string,
  duration: number,
  steam_id: string,
}>((props) => {
  const { t: $t, locale } = useI18n()
  return () => <div class="flex">
    <div>
      <img src="https://via.placeholder.com/80" alt="player avatar" class="rounded-full" />
    </div>
    <div class="flex flex-col justify-around flex-auto ml-2">
      <div class="flex justify-between"><span class="text-2xl">{props.nickname}</span> <span class="text-sm">{ $t('ui.steam_id') }: {props.steam_id}</span></div>
      <div class="flex justify-between"><span>{ $t('ui.role_name') }: {props.role_name}</span></div>
      <div class="flex justify-between">
        <span>{ $t('ui.duration') }: {(props.duration / 3600).toFixed(1)}h</span>
        <span><button>{ $t('ui.swtich') }</button><ButtonLanguage class="ml-1" current={locale.value as any} /></span>
      </div>
    </div>
  </div>
}, {
  name: "PlayerCard",
  props: ["nickname", "role_name", "duration", "steam_id"],
})

export const NumberInfo = defineComponent<{
  value: number,
  title: string,
}>((props) => {
  return () => <div class="flex flex-col items-center text-center bg-gray m-1 p-1">
    <span class="text-2xl font-bold">{props.value}</span>
    <span class="test-xs">{props.title}</span>
  </div>
}, {
  name: "NumberInfo",
  props: ["value", "title"]
})

export const NumberInfoBanner = defineComponent<{
  value: number,
  text_keypath: string,
}>((props) => {
  return () => <div class="text-center bg-gray m-1 p-3">
    <i18n-t keypath={props.text_keypath} plural={props.value}>
      <span class="text-2xl font-bold text-red">{props.value}</span>
    </i18n-t>
  </div>
}, {
  name: "NumberInfoBanner",
  props: ["value", "text_keypath"],
})

export const ButtonLanguage = defineComponent<{
  current: "en" | "cn" | "ja",
}>((props) => {
  const i18n = useI18n()
  const next_lang = (current: "en" | "cn" | "ja") => {
    switch (current) {
      case "en": return "cn"
      case "cn": return "ja"
      case "ja": return "en"
    }
  }
  return () => <a href='#' onClick={() => {i18n.locale.value = next_lang(props.current)}}>{props.current}</a>
}, {
  name: "ButtonLanguage",
  props: ["current"],
})

export const HealthBar = defineComponent<{
  title: string,
  status: {
    current: number,
    max: number,
    base: number,
  },
  color: 'red' | 'green' | 'blue'
}>((props) => {
  const percent = props.status.current / props.status.max * 100
  const style = {
    red: "bg-red-400",
    green: "bg-green-400",
    blue: "bg-blue-400",
  }
  return () => <tr class="m-1 p-1">
    <td class="w-1 text-nowrap"><span>{props.title}</span></td>
    <td class="p-1"><div class="bg-gray-200 h-1">
      <div class={style[props.color]} style={{ width: `${percent}%`, height: "90%" }}></div>
    </div></td>
    <td class="text-right w-1 text-nowrap"><span>{props.status.current}/{props.status.max}</span></td>
  </tr>
}, {
  name: "HealthBar",
  props: ["title", "status", "color"]
})
