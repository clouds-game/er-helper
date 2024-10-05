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
  <div class="grid grid-auto-cols-8">
    <div v-for="b in bosses">{{ t(`db.boss.name.${b.id}`) }}</div>
  </div>
</template>
