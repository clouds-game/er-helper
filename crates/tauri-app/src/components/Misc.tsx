import { defineComponent } from "vue"

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
      <div class="flex justify-between"><span>Player: {props.nickname}</span> <span class="bg-gray">Steam ID: {props.steam_id}</span></div>
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
