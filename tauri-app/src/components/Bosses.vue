<script setup lang="tsx">
import { computed } from 'vue';
import { BossInfo } from '../lib/utils'
import { useI18n } from 'vue-i18n';
import { BossDB } from '../lib/db';

const props = defineProps<{
  data: BossInfo[]
}>()

const bosses = computed(() => props.data)

const { t } = useI18n({
  messages: BossDB.i18n()
})

</script>

<template>
  <div class="grid grid-cols-6">
    <div class="m-1 bg-gray-200" v-for="b in bosses">
      <div>{{ t(`db.boss.name.${b.id}`) }}</div>
      <div class="text-gray text-sm">{{ t(`db.boss.map_name.${b.map_id}`) }}</div>
    </div>
  </div>
</template>
