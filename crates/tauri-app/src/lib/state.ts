import { invoke } from "@tauri-apps/api/core";
import { defineStore } from "pinia";
import { ref, watch } from "vue";

export const useState = defineStore("state", () => {
  console.log("state store created")
  const metadata = ref({
    exists: false,
    last_modified: 0,
    size: 0,
  })
  const basic_names = ref({
    nickname: 'LOADING...',
    role_name: '',
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
  const time = ref({
    current: new Date(),
    latest: new Date(0),
  })

  const update = async () => {
    try {
      metadata.value = await invoke("get_metadata")
      basic_names.value = await invoke("get_basic_info")
      basic_number.value = await invoke("get_player_info")
      time.value.current = new Date(metadata.value.last_modified * 1000)
    } catch (e) {
      console.error(e)
    }
  }

  watch(() => metadata.value.last_modified, () => {
    time.value.latest = new Date(metadata.value.last_modified * 1000)
  })

  return {
    metadata,
    basic_names,
    basic_number,
    time,
    update
  }
})
