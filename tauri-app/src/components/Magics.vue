<script setup lang="ts">
import { ref, watch } from 'vue'
import { MagicInfo, useAssets } from '../lib/state'
import { useI18n } from 'vue-i18n'
import { GoodsDB } from '../lib/db'

const assets = useAssets()

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
  const icons = await assets.load_icons(magics.map(w => w.icon_id ?? 0))
  magics.forEach((w, i) => {
    if (EMPTY_IDS.includes(w.id)) icons[i] = undefined
  })
  magics_icons.value = icons.map(i => i ?? assets.EMPTY_IMAGE)
}

const magics_icons = ref<string[]>([])
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
      <div v-for="magic, i in magics" :key="magic.id" class="m-1 bg-gray-200">
        <img class="rounded-full w-full h-auto" :src="magics_icons[i]" :alt="magic.name" />
        <div class="text-xs text-center" v-if="showTitle">{{ magic_name(magic.id) }}</div>
      </div>
    </div>
  </div>
</template>
