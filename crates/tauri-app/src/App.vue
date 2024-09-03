<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { PlayerCard, NumberInfo } from './components/Misc'

const basic_names = {
  nickname: 'hello',
  game_name: 'miao',
  duration: 10000,
  steam_id: 'AABBCCDD',
}
const basic_number = {
  level: 900,
  rune: 300_000,
  boss: 99,
  place: 250,
}

</script>

<template>
  <div class="m-1 grid grid-cols-4">
    <div class="col-span-4">
      <PlayerCard :nickname="basic_names.nickname" :game_name="basic_names.game_name" :duration="basic_names.duration" :steam_id="basic_names.steam_id" />
    </div>
    <NumberInfo title="Level" :value="basic_number.level" />
    <NumberInfo title="Rune" :value="basic_number.rune" />
    <NumberInfo title="Boss" :value="basic_number.boss" />
    <NumberInfo title="Place" :value="basic_number.place" />
  </div>
</template>

<style scoped>
</style>
