import { invoke } from "@tauri-apps/api/core"
import { defineStore } from "pinia"
import { reactive, ref, watch } from "vue"
import { GoodsDB, WeaponDB } from './db'

export interface WeaponInfo {
  id: number
  level: number
  icon_id?: number
  wep_type?: number
}
export interface MagicInfo {
  id: number
  icon_id?: number
}

const array_new = (length: number) => Array.from({ length }, () => 0)

export const useState = defineStore("state", () => {
  console.log("state store created")
  const metadata = ref({
    exists: false,
    last_modified: 0,
    size: 0,
  })
  const nickname = ref(localStorage.getItem('nickname'))
  const basic_info = ref({
    role_name: 'LOADING...',
    duration: 0,
    steam_id: '',
    level: 0,
    rune: 0,
    boss: 0,
    grace: 0,
    death: 0,
    attrs: array_new(8),
    hp: array_new(3),
    fp: array_new(3),
    sp: array_new(3),
  })
  const equipped_info = ref({
    lefthand: [] as WeaponInfo[],
    righthand: [] as WeaponInfo[],
    arrows: [] as WeaponInfo[],
    bolts: [] as WeaponInfo[],
    magics: [] as MagicInfo[],
  })
  const time = ref({
    queried: new Date(0),
    current: new Date(),
    latest: new Date(0),
  })

  const update = async () => {
    try {
      metadata.value = await invoke("get_metadata")
      basic_info.value = await invoke("get_basic_info")
      if (nickname.value == null) {
        nickname.value = basic_info.value.role_name + '#' + basic_info.value.steam_id.slice(-4)
      }
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
  const update_goods_info = (g: MagicInfo) => {
    const goods = GoodsDB.get(g.id)
    if (goods) {
      g.icon_id = goods.icon_id
    }
    return g
  }

  const update_equipped_items = async () => {
    try {
      equipped_info.value = await invoke("get_equipped_info")
      equipped_info.value.lefthand = equipped_info.value.lefthand.map(update_weapon_info)
      equipped_info.value.righthand = equipped_info.value.righthand.map(update_weapon_info)
      equipped_info.value.arrows = equipped_info.value.arrows.map(update_weapon_info)
      equipped_info.value.bolts = equipped_info.value.bolts.map(update_weapon_info)
      equipped_info.value.magics = equipped_info.value.magics.map(update_goods_info)
    } catch (e) {
      console.error(e)
    }
  }

  watch(() => metadata.value.last_modified, () => {
    time.value.latest = new Date(metadata.value.last_modified * 1000)
  })
  watch(nickname, (new_nickname) => {
    if (new_nickname == null)
      localStorage.removeItem('nickname')
    else
      localStorage.setItem('nickname', new_nickname)
  })

  return {
    metadata,
    basic_info,
    equipped_info,
    time,
    nickname,
    update,
    update_equipped_items,
  }
})

export const useAssets = defineStore("assets", () => {
  // TODO: LRU of icons?
  const icons = reactive(new Map<number, string>())
  const EMPTY_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='

  const load_icons = async (icon_ids: (number | undefined)[]) => {
    const to_load_ids = icon_ids.filter(id => id != null).filter(id => !icons.has(id))
    const loaded_icons = await invoke<string[]>('get_icons', { icon_ids: Array.from(new Set(to_load_ids)) })
    to_load_ids.forEach((id, i) => {
      icons.set(id, loaded_icons[i])
    })
    return icon_ids.map(id => id != null ? icons.get(id) : undefined)
  }

  return {
    icons,
    EMPTY_IMAGE,
    load_icons,
  }
})
