import { BossDB, GoodsDB, GoodsType, GraceDB, WeaponDB } from "./db"

export interface WeaponInfo {
  id: number
  level: number
  icon_id?: number
  wep_type?: number
}
export interface MagicInfo {
  id: number
  type?: GoodsType
  icon_id?: number
}
export interface BossInfo {
  id: number
  flag_id?: number
  defeated?: boolean
  map_id?: number
}
export interface GraceInfo {
  id: number
  flag_id?: number
  activated?: boolean
  map_id?: number
}


export const array_new = (length: number) => Array.from({ length }, () => 0)

export const resolve_weapon_info = (w: WeaponInfo) => {
  const weapon = WeaponDB.get(w.id)
  if (weapon) {
    w.icon_id = weapon.icon_id
    w.wep_type = weapon.type
  }
  return w
}
export const resolve_goods_info = (g: MagicInfo) => {
  const goods = GoodsDB.get(g.id)
  if (goods) {
    g.icon_id = goods.icon_id
    g.type = goods.type
  }
  return g
}
export const resolve_boss_info = (id: number) => {
  const b = { id } as BossInfo;
  const boss = BossDB.get(id)
  if (boss) {
    b.flag_id = boss.eventflag_id
    b.map_id = boss.map_text_id
  }
  return b
}
export const resolve_grace_info = (id: number) => {
  const g = { id } as GraceInfo;
  const grace = GraceDB.get(g.id)
  if (grace) {
    g.flag_id = grace.eventflag_id
    g.map_id = grace.map_id
  }
  return g
}
