<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { computed, onMounted, onUnmounted } from 'vue'
import { Banner, PlayerCard, NumberInfo, NumberInfoBanner, HealthBar } from './components/Misc'
import * as timeago from 'timeago.js'
import { useState } from './lib/state'
import { useI18n } from 'vue-i18n'
import Weapons from './components/Weapons.vue'
import Magics from './components/Magics.vue'
import Bosses from './components/Bosses.vue'

const { t, locale } = useI18n()
const state = useState()

let timer: number | undefined
onMounted(async () => {
  state.update()
  timer = setInterval(() => {
    state.update()
  }, 3000)
  console.log(state.time.current)
  console.log(state.equipped_info)
})

onUnmounted(() => {
  clearInterval(timer)
})

const timeago_locale = computed(() => {
  return {
    en: "en_US",
    cn: "zh_CN",
    ja: "ja_JP",
  }[locale.value]
})

const latest_time_str = computed(() => {
  return timeago.format(state.time.latest, timeago_locale.value)
})

const basic_names = computed(() => ({
  // nickname: state.basic_info.nickname,
  role_name: state.basic_info.role_name,
  duration: state.basic_info.duration,
  steam_id: state.basic_info.steam_id,
}))

const basic_number = computed(() => ({
  level: state.basic_info.level,
  rune: state.basic_info.rune,
  boss: state.basic_info.boss,
  grace: state.basic_info.grace,
  death: state.basic_info.death,
}))

const add_points = computed(() => ({
  vigor: state.basic_info.attrs[0],
  mind: state.basic_info.attrs[1],
  endurance: state.basic_info.attrs[2],
  strength: state.basic_info.attrs[3],
  dexterity: state.basic_info.attrs[4],
  intelligence: state.basic_info.attrs[5],
  faith: state.basic_info.attrs[6],
  arcane: state.basic_info.attrs[7],
}))

const role_status = computed(() => ({
  hp: {
    current: state.basic_info.hp[0],
    max: state.basic_info.hp[1],
    base: state.basic_info.hp[2],
  },
  fp: {
    current: state.basic_info.fp[0],
    max: state.basic_info.fp[1],
    base: state.basic_info.fp[2],
  },
  sp: {
    current: state.basic_info.sp[0],
    max: state.basic_info.sp[1],
    base: state.basic_info.sp[2],
  },
}))

</script>

<template>
  <div class="m-1 grid grid-cols-4">
    <Banner class="col-span-4" :level="state.time.current.getTime() === state.time.latest.getTime() ? 'info' : 'warn'" v-if="state.time.latest.getTime()">
      {{ t('message.update_at', [latest_time_str]) }}
    </Banner>
    <Banner class="col-span-4" level="error" v-else>
      {{ t('message.save_file_not_found') }}
    </Banner>
    <div class="col-span-4">
      <PlayerCard :nickname="state.nickname ?? ''" :role_name="basic_names.role_name" :duration="basic_names.duration" :steam_id="basic_names.steam_id" />
    </div>
    <NumberInfo :title="t('game.level')" :value="basic_number.level" />
    <NumberInfo :title="t('ui.current_runes')" :value="basic_number.rune" />
    <NumberInfo :title="t('ui.defeated_boss')" :value="basic_number.boss" />
    <NumberInfo :title="t('ui.unlocked_graces')" :value="basic_number.grace" />
    <NumberInfoBanner class="col-span-4" text_keypath="message.death_times" :value="basic_number.death" />
    <div class="m-1 col-span-2">
      <div>{{ t("ui.status") }}</div>
      <table class="w-full">
        <HealthBar :title="t('game.hp')" :status="role_status.hp" color="red" />
        <HealthBar :title="t('game.fp')" :status="role_status.fp" color="blue" />
        <HealthBar :title="t('game.sp')" :status="role_status.sp" color="green" />
      </table>
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("game.memory_slots", 6) }}</div>
      <Magics :data="state.equipped_info.magics" />
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("ui.equips", 20) }}</div>
      <Weapons :data="state.equipped_info.righthand.concat(state.equipped_info.arrows)" />
      <Weapons :data="state.equipped_info.lefthand.concat(state.equipped_info.bolts)" />
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("game.main_attribute") }}</div>
      <div class="bg-gray-300 p-2 rounded shadow">
        <div class="flex justify-between" v-for="attr in (['vigor', 'mind', 'endurance', 'strength', 'dexterity', 'intelligence', 'faith', 'arcane'] as const)">
          <span>{{ t(`game.attr_${attr}`, `${attr}`) }}:</span> <span>{{ add_points[attr] }}</span>
        </div>
      </div>
    </div>
    <div class="m-1 col-span-4">
      <div>{{ t("game.boss") }}</div>
      <Bosses :data="state.events_info.boss" />
    </div>
  </div>
</template>

<style>
body {
  font-family: 'Noto Sans', sans-serif;
  background-color: #f0f2f5;
  color: #333;
}
</style>
