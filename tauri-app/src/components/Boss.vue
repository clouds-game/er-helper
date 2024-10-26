<script setup lang="tsx">
import { computed } from 'vue';
import { BossInfo } from '../lib/utils';
import { BossDB } from '../lib/db';
import { useI18n } from 'vue-i18n';

const props = defineProps<{
  data: BossInfo
}>()

const boss_id = computed(() => props.data.id)
const boss_info = computed(() => BossDB.get(boss_id.value))
const { t } = useI18n({
  messages: BossDB.i18n()
})

</script>

<template>
  <div>
    <div>Boss: {{ t(`db.boss.name.${boss_id}`) }} ({{ boss_id }})</div>
    <div>FlagID: {{ boss_info?.eventflag_id }}</div>
  </div>
</template>
