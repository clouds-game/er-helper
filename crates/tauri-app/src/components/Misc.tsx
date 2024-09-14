import { defineComponent } from "vue"

export const Banner = defineComponent<{
  content?: string,
  level: "warn" | "info" | "error",
}>((props, i) => {
  const style = {
    warn: "bg-yellow-200",
    info: "bg-blue-200",
    error: "bg-red-200",
  }
  return () => <div class={`text-center mb-1 ${style[props.level]}`}>
    { props.content }
    { i.slots.default && i.slots.default() }
  </div>
}, {
  name: "Banner",
  props: ['content', 'level'],
})

export const PlayerCard = defineComponent<{
  nickname: string,
  game_name: string,
  duration: number,
  steam_id: string,
}>((props) => {
  return () => <div class="flex">
    <div>
      <img src="https://via.placeholder.com/80" alt="player avatar" class="rounded-full" />
    </div>
    <div class="flex flex-col justify-around flex-auto ml-2">
      <div class="flex justify-between"><span class="text-2xl">{props.nickname}</span> <span class="text-sm">Steam ID: {props.steam_id}</span></div>
      <div class="flex justify-between"><span>Game: {props.game_name}</span></div>
      <div class="flex justify-between"><span>Duration: {props.duration}</span> <button>switch</button></div>
    </div>
  </div>
}, {
  name: "PlayerCard",
  props: ["nickname", "game_name", "duration", "steam_id"]
})

export const NumberInfo = defineComponent<{
  value: number,
  title: string,
}>((props) => {
  return () => <div class="flex flex-col items-center bg-gray m-1 p-1">
    <span class="text-2xl">{props.value}</span>
    <span>{props.title}</span>
  </div>
}, {
  name: "NumberInfo",
  props: ["value", "title"]
})

export const NumberInfoBanner = defineComponent<{
  value: number,
  prefix_text: string,
  suffix_text: string,
}>((props) => {
  return () => <div class="text-center bg-gray m-1 p-3">
    {props.prefix_text}
    <span class="text-2xl text-red">{props.value}</span>
    {props.suffix_text}
  </div>
}, {
  name: "NumberInfoBanner",
  props: ["value", "prefix_text", "suffix_text"]
})
