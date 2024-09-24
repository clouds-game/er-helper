<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { computed, onMounted, onUnmounted } from 'vue';
import { Banner, PlayerCard, NumberInfo, NumberInfoBanner, WeaponInfoBanner } from './components/Misc'
import * as timeago from 'timeago.js';
import { useState } from './lib/state';
import { useI18n } from 'vue-i18n';

const { t, locale } = useI18n()
const state = useState()

let timer: number | undefined
onMounted(async () => {
  state.update()
  state.update_equipped_weapons()
  timer = setInterval(() => {
    state.update()
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
  }[locale.value]
})

const latest_time_str = computed(() => {
  return timeago.format(state.time.latest, timeago_locale.value)
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
    <NumberInfo :title="t('ui.level')" :value="state.basic_number.level" />
    <NumberInfo :title="t('ui.runes')" :value="state.basic_number.rune" />
    <NumberInfo :title="t('ui.boss')" :value="state.basic_number.boss" />
    <NumberInfo :title="t('ui.graces')" :value="state.basic_number.grace" />
    <NumberInfoBanner class="col-span-4" text_keypath="message.death_times" :value="state.basic_number.death" />
  </div>
  <div class="m-1 grid grid-cols-2" >
    <WeaponInfoBanner v-if="state.equipped_weapon_infos.lefthand" :weapon_infos="state.equipped_weapon_infos.lefthand"></WeaponInfoBanner>
    <WeaponInfoBanner v-if="state.equipped_weapon_infos.righthand" :weapon_infos="state.equipped_weapon_infos.righthand"></WeaponInfoBanner>
  </div>
</template>

<style>
body {
  font-family: 'Noto Sans', sans-serif;
  background-color: #f0f2f5;
  color: #333;
}
</style>
