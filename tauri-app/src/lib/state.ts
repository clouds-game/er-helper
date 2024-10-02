import { invoke } from "@tauri-apps/api/core"
import { defineStore } from "pinia"
import { ref, watch } from "vue"
import { WeaponDB } from './db'

export interface WeaponInfo {
  id: number
  level: number
  icon_id?: number
  wep_type?: number
}

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
    grace: 0,
    death: 0,
  })
  const equipped_weapon_infos = ref<{
    lefthand: WeaponInfo[];
    righthand: WeaponInfo[];
  }>
  ({
    lefthand: [],
    righthand: [],
  })
  const time = ref({
    queried: new Date(0),
    current: new Date(),
    latest: new Date(0),
  })

  const update = async () => {
    try {
      metadata.value = await invoke("get_metadata")
      basic_names.value = await invoke("get_basic_info")
      basic_number.value = await invoke("get_player_info")
      time.value.current = new Date(metadata.value.last_modified * 1000)
      time.value.queried = new Date()
    } catch (e) {
      console.error(e)
    }
  }

  const update_weapon_info = (w: WeaponInfo) => {
    const weapon = WeaponDB.get(w.id)
    if (weapon) {
      w.icon_id = weapon.icon_id
      w.wep_type = weapon.type
    }
    return w
  }

  const update_equipped_weapons = async () => {
    try {
      equipped_weapon_infos.value = await invoke("get_equipped_weapon_info")
      equipped_weapon_infos.value.lefthand = equipped_weapon_infos.value.lefthand.map(update_weapon_info)
      equipped_weapon_infos.value.righthand = equipped_weapon_infos.value.righthand.map(update_weapon_info)
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
    equipped_weapon_infos,
    time,
    update,
    update_equipped_weapons
  }
})
