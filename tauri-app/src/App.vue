<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { computed, onMounted, onUnmounted } from 'vue';
import { Banner, PlayerCard, NumberInfo, NumberInfoBanner } from './components/Misc'
import * as timeago from 'timeago.js';
import { useState } from './lib/state';
import { useI18n } from 'vue-i18n';
import Weapons from './components/Weapons.vue';

const { t, locale } = useI18n()
const state = useState()

let timer: number | undefined
onMounted(async () => {
  state.update()
  state.update_equipped_weapons()
  timer = setInterval(() => {
    state.update()
    state.update_equipped_weapons()
  }, 3000)
  console.log(state.time.current)
  console.log(state.equipped_weapon_infos)
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

const add_points = computed(() => {
  return {
    vigor: 100,
    mind: 100,
    endurance: 100,
    strength: 100,
    dexterity: 100,
    intelligence: 100,
    faith: 100,
    arcane: 100,
  }
})

</script>

<template>
  <div class="m-1 grid grid-cols-4">
    <Banner class="col-span-4" :level="state.time.current.getTime() === state.time.latest.getTime() ? 'info' : 'warn'" v-if="state.time.latest">
      {{ t('message.update_at', [latest_time_str]) }}
    </Banner>
    <div class="col-span-4">
      <PlayerCard :nickname="state.basic_names.nickname" :role_name="state.basic_names.role_name" :duration="state.basic_names.duration" :steam_id="state.basic_names.steam_id" />
    </div>
    <NumberInfo :title="t('game.level')" :value="state.basic_number.level" />
    <NumberInfo :title="t('ui.current_runes')" :value="state.basic_number.rune" />
    <NumberInfo :title="t('ui.defeated_boss')" :value="state.basic_number.boss" />
    <NumberInfo :title="t('ui.unlocked_graces')" :value="state.basic_number.grace" />
    <NumberInfoBanner class="col-span-4" text_keypath="message.death_times" :value="state.basic_number.death" />
    <div class="m-1 col-span-2">
      <div>{{ t("ui.status") }}</div>
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("game.memory_slots", 6) }}</div>
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("ui.equips", 20) }}</div>
      <Weapons :weapons="state.equipped_weapon_infos.righthand" />
      <Weapons :weapons="state.equipped_weapon_infos.lefthand" />
    </div>
    <div class="m-1 col-span-2">
      <div>{{ t("game.main_attribute") }}</div>
      <div class="bg-gray-300 p-2 rounded shadow">
        <div class="flex justify-between" v-for="attr in (['vigor', 'mind', 'endurance', 'strength', 'dexterity', 'intelligence', 'faith', 'arcane'] as const)">
          <span>{{ t(`game.attr_${attr}`) }}:</span> <span>{{ add_points[attr] }}</span>
        </div>
      </div>
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
