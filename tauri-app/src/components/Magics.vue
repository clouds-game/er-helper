<script setup lang="ts">
import { invoke } from '@tauri-apps/api/core';
import { ref, watch } from 'vue';
import { MagicInfo } from '../lib/state';
import { useI18n } from 'vue-i18n';
import { GoodsDB } from '../lib/db';

const EMPTY_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
const EMPTY_IDS = [4294967295]

export interface Magic {
  id: number
  name?: string
  desc?: string
  icon_id?: number
  image?: string
}

const props = defineProps<{
  magics: MagicInfo[]
}>()

const load_magics = async (...magics: Magic[]) => {
  magics.forEach(w => {
    if (w.image == undefined && EMPTY_IDS.includes(w.id)) {
      w.image = EMPTY_IMAGE
    }
  })
  try {
    const icon_ids = Array.from(new Set(magics.filter(w => w.image == undefined).map(w => w.icon_id ?? 0)))
    if (icon_ids.length == 0) {
      return
    }
    const icons = await invoke<string[]>('get_icons', { icon_ids })
    const icon_map = new Map(icons.map((icon, i) => [icon_ids[i], icon]))
    magics.forEach(w => {
      if (w.image == undefined) {
        w.image = icon_map.get(w.icon_id ?? 0);
      }
    })
  } catch (e) {
    console.error(e)
  }
}

const magics = ref<Magic[]>([])
watch(() => props.magics, async (new_value) => {
  magics.value = new_value.filter(m => !EMPTY_IDS.includes(m.id))
  await load_magics(...magics.value)
})

const showTitle = ref(false)

const magic_name = (id: number) => {
  if (EMPTY_IDS.includes(id)) {
    return ""
  } else {
    return t(`db.goods.name.${id}`, ''+id)
  }
}

const { t } = useI18n({
  messages: GoodsDB.i18n()
})
</script>


<template>
  <div>
    <div class="grid grid-cols-6" @mouseover="showTitle = true" @mouseleave="showTitle=false">
      <div v-for="magic in magics" :key="magic.id" class="m-1 bg-gray-200">
        <img class="rounded-full w-full h-auto" :src="magic.image" :alt="magic.name" />
        <div class="text-xs text-center" v-if="showTitle">{{ magic_name(magic.id) }}</div>
      </div>
    </div>
  </div>
</template>
