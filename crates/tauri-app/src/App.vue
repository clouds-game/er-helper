<script setup lang="ts">
// This starter template is using Vue 3 <script setup> SFCs
// Check out https://vuejs.org/api/sfc-script-setup.html#script-setup
import { computed, onMounted } from 'vue';
import { Banner, PlayerCard, NumberInfo, NumberInfoBanner } from './components/Misc'
import * as timeago from 'timeago.js';
import { useState } from './lib/state';

const state = useState()

onMounted(async () => {
  state.update()
  console.log(state.time.current)
})

const latest_time_str = computed(() => {
  return timeago.format(state.time.latest)
})

</script>

<template>
  <div class="m-1 grid grid-cols-4">
    <Banner class="col-span-4" :level="state.time.current.getTime() === state.time.latest.getTime() ? 'info' : 'warn'" v-if="state.time.latest">
      updated {{ latest_time_str }}
    </Banner>
    <div class="col-span-4">
      <PlayerCard :nickname="state.basic_names.nickname" :game_name="state.basic_names.game_name" :duration="state.basic_names.duration" :steam_id="state.basic_names.steam_id" />
    </div>
    <NumberInfo title="Level" :value="state.basic_number.level" />
    <NumberInfo title="Rune" :value="state.basic_number.rune" />
    <NumberInfo title="Boss" :value="state.basic_number.boss" />
    <NumberInfo title="Place" :value="state.basic_number.place" />
    <NumberInfoBanner class="col-span-4" prefix_text="You died for " suffix_text=" times." :value="state.basic_number.death" />
  </div>
</template>

<style scoped>
</style>
