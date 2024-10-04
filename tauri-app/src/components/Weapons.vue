<script setup lang="ts">
import { ref, watch } from 'vue';
import { useAssets, WeaponInfo } from '../lib/state';
import { useI18n } from 'vue-i18n';
import { WeaponDB } from '../lib/db';

const EMPTY_IDS = [110000, 4294967200]

const assets = useAssets()

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
  const icons = await assets.load_icons(weapon.map(w => w.icon_id ?? 0))
  weapon.forEach((w, i) => {
    if (EMPTY_IDS.includes(w.id)) icons[i] = undefined
  })
  weapon_icons.value = icons.map(i => i ?? assets.EMPTY_IMAGE)
}

const weapon_icons = ref<string[]>([])
const weapons = ref<Weapon[]>([])
watch(() => props.weapons, async (new_weapons) => {
  weapons.value = new_weapons
  await load_weapons(...weapons.value)
})

const showTitle = ref(false)

const weapon_name = (id: number) => {
  if (EMPTY_IDS.includes(id)) {
    return ""
  } else {
    return t(`db.weapon.name.${id}`, ''+id)
  }
}

const { t } = useI18n({
  messages: WeaponDB.i18n()
})
</script>


<template>
  <div>
    <div class="grid grid-cols-5" @mouseover="showTitle = true" @mouseleave="showTitle=false">
      <div v-for="weapon, i in weapons" :key="weapon.id" class="m-1 bg-gray-200">
        <img class="rounded-full w-full h-auto" :src="weapon_icons[i]" :alt="weapon.name" />
        <div class="text-xs text-center" v-if="showTitle">{{ weapon_name(weapon.id) }}</div>
      </div>
    </div>
  </div>
</template>
