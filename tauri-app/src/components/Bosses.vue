<script setup lang="tsx">
import { computed, ref } from 'vue'
import { BossInfo } from '../lib/utils'
import { useI18n } from 'vue-i18n'
import { BossDB } from '../lib/db'
import Card from './Card.vue'
import Boss from './Boss.vue'

const props = defineProps<{
  data: BossInfo[]
}>()

const bosses = computed(() => props.data)

const view_boss = ref<BossInfo>()
const { t } = useI18n({
  messages: BossDB.i18n()
})

</script>

<template>
  <div class="grid grid-cols-6">
    <Card class="col-span-6" v-if="view_boss">
      <Boss :data="view_boss" />
    </Card>
    <div class="m-1 bg-gray-200" @click="view_boss=b" v-for="b in bosses">
      <div>{{ t(`db.boss.name.${b.id}`) }}</div>
      <div class="text-gray text-sm">{{ t(`db.boss.map_name.${b.map_id}`) }}</div>
    </div>
  </div>
</template>
