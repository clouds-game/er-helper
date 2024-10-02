
<script setup lang="ts">
import { invoke } from '@tauri-apps/api/core';
import { ref, watch } from 'vue';
import { WeaponInfo } from '../lib/state';
import { useI18n } from 'vue-i18n';
import { WeaponDB } from '../lib/db';

export interface Weapon {
  id: number
  level?: number
  name?: string
  desc?: string
  icon_id?: number
  image?: string
}

const props = defineProps<{
  weapons: WeaponInfo[]
}>()

const load_weapons = async (...weapon: Weapon[]) => {
  try {
    const icon_ids = Array.from(new Set(weapon.filter(w => w.image == undefined && w.icon_id != undefined).map(w => w.icon_id)))
    if (icon_ids.length == 0) {
      return
    }
    console.log("icon_ids", icon_ids, weapon)
    const icons = await invoke<string[]>('get_icons', { icon_ids })
    console.log("icons", icons)
    const icon_map = new Map(icons.map((icon, i) => [icon_ids[i], icon]))
    weapon.forEach(w => {
      if (w.image == undefined) {
        w.image = icon_map.get(w.icon_id);
      }
    })
  } catch (e) {
    console.error(e)
  }
}

const weapons = ref<Weapon[]>([])
watch(() => props.weapons, async (new_weapons) => {
  weapons.value = new_weapons
  await load_weapons(...weapons.value)
})

const showTitle = ref(false)

const { t } = useI18n({
  messages: WeaponDB.i18n()
})
</script>


<template>
  <div>
    <div class="grid grid-cols-6" @mouseover="showTitle = true" @mouseleave="showTitle=false">
      <div v-for="weapon in weapons" :key="weapon.id" class="m-1 bg-gray-200">
        <img class="rounded-full w-full h-auto" :src="weapon.image" :alt="weapon.name" />
        <div class="text-xs text-center" v-if="showTitle">{{ t(`db.weapon.name.${weapon.id}`) }}</div>
      </div>
    </div>
  </div>
</template>
