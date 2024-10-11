import { defineStore } from "pinia"
import { reactive, ref, watch } from "vue"
import { array_new, BossInfo, GraceInfo, MagicInfo, resolve_boss_info, resolve_goods_info, resolve_grace_info, resolve_weapon_info, WeaponInfo } from "./utils"
import { commands } from "./bindings"

export type { MagicInfo, WeaponInfo }

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
  const events_info = ref({
    boss: [] as BossInfo[],
    grace: [] as GraceInfo[],
  })
  const time = ref({
    queried: new Date(0),
    current: new Date(),
    latest: new Date(0),
  })

  const update_basic_info = async () => {
    try {
      metadata.value = await commands.getMetadata()
      basic_info.value = await commands.getBasicInfo(null)
      if (nickname.value == null) {
        nickname.value = basic_info.value.role_name + '#' + basic_info.value.steam_id.slice(-4)
      }
      time.value.current = new Date(metadata.value.last_modified * 1000)
      time.value.queried = new Date()
    } catch (e) {
      console.error(e)
    }
  }

  const update_equipped_items = async () => {
    try {
      equipped_info.value = await commands.getEquippedInfo()
      equipped_info.value.lefthand = equipped_info.value.lefthand.map(resolve_weapon_info)
      equipped_info.value.righthand = equipped_info.value.righthand.map(resolve_weapon_info)
      equipped_info.value.arrows = equipped_info.value.arrows.map(resolve_weapon_info)
      equipped_info.value.bolts = equipped_info.value.bolts.map(resolve_weapon_info)
      equipped_info.value.magics = equipped_info.value.magics.map(resolve_goods_info)
    } catch (e) {
      console.error(e)
    }
  }

  const update_events_info = async () => {
    try {
      const info = await commands.getEventsInfo()
      events_info.value.boss = info.boss.map(resolve_boss_info)
      events_info.value.grace = info.grace.map(resolve_grace_info)
    } catch (e) {
      console.error(e)
    }
  }

  const update = async () => {
    await Promise.all([
      update_basic_info(),
      update_equipped_items(),
      update_events_info(),
    ])
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
    events_info,
    time,
    nickname,
    update_basic_info,
    update_equipped_items,
    update_events_info,
    update,
  }
})

export const useAssets = defineStore("assets", () => {
  // TODO: LRU of icons?
  const icons = reactive(new Map<number, string>())
  const EMPTY_IMAGE = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='

  const load_icons = async (icon_ids: (number | undefined)[]) => {
    const to_load_ids = icon_ids.filter(id => id != null).filter(id => !icons.has(id))
    if (to_load_ids.length > 0) {
      const loaded_icons = await commands.getIcons(Array.from(new Set(to_load_ids)))
      to_load_ids.forEach((id, i) => {
        icons.set(id, loaded_icons[i])
      })
    }
    return icon_ids.map(id => id != null ? icons.get(id) : undefined)
  }

  return {
    icons,
    EMPTY_IMAGE,
    load_icons,
  }
})
