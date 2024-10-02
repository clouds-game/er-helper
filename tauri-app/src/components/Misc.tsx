import { defineComponent } from "vue"
import { useI18n } from "vue-i18n"

const i18n = {
  en: {
    steam_id: "Steam ID",
    role_name: "Role Name",
    duration: "Duration",
    swtich: "Switch Role",
  },
  cn: {
    steam_id: "Steam ID",
    role_name: "当前角色",
    duration: "游戏时长",
    swtich: "切换角色",
  },
  ja: {
    steam_id: "Steam ID",
    role_name: "役職",
    duration: "ゲーム時間",
    swtich: "役職を切り替える",
  },
}

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
  const { t: $t, locale } = useI18n({ messages: i18n })
  return () => <div class="flex">
    <div>
      <img src="https://via.placeholder.com/80" alt="player avatar" class="rounded-full" />
    </div>
    <div class="flex flex-col justify-around flex-auto ml-2">
      <div class="flex justify-between"><span class="text-2xl">{props.nickname}</span> <span class="text-sm">{ $t('steam_id') }: {props.steam_id}</span></div>
      <div class="flex justify-between"><span>{ $t('role_name') }: {props.role_name}</span></div>
      <div class="flex justify-between">
        <span>{ $t('duration') }: {(props.duration / 3600).toFixed(1)}h</span>
        <span><button>{ $t('swtich') }</button><ButtonLanguage class="ml-1" current={locale.value} /></span>
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
