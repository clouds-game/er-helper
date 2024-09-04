<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { onMounted, ref } from 'vue';
import { PlayerCard, NumberInfo, NumberInfoBanner } from './components/Misc'
import { invoke } from '@tauri-apps/api/core';

const basic_names = ref({
  nickname: 'LOADING...',
  game_name: '',
  duration: 0,
  steam_id: '',
})
const basic_number = ref({
  level: 0,
  rune: 0,
  boss: 0,
  place: 0,
  death: 0,
})

onMounted(async () => {
  basic_names.value = await invoke("get_basic_info")
  basic_number.value = await invoke("get_player_info")
})

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
    <NumberInfoBanner class="col-span-4" prefix_text="You died for " suffix_text=" times." :value="basic_number.death" />
  </div>
</template>

<style scoped>
</style>
