import _WeaponSource from "../../assets/weapon.out.json"
import _GraceSource from "../../assets/grace.out.json"
import _BossSource from "../../assets/boss.out.json"


export type Lang = 'engus' | 'jpnjp' | 'zhocn'
export class Database<D extends IItem, T extends Text> {
  constructor(public name: string, public source: ISource<D, T>) {}

  get(id: number): D | undefined {
    return this.source.data.find((d) => d.id === id)
  }

  getText(id: number, lang: Lang): string | null {
    return this.source.text[lang]?.name[id] ?? null
  }

  i18n(): any {
    return {
      'cn': { 'db': { [this.name]: this.source.text.zhocn } },
      'en': { 'db': { [this.name]: this.source.text.engus } },
      'ja': { 'db': { [this.name]: this.source.text.jpnjp } },
    }
  }
}

export const WeaponDB: Database<WeaponInfo, Text> = new Database("weapon", _WeaponSource)
export const GraceDB: Database<GraceInfo, TextWithMap> = new Database("grace", _GraceSource)
export const BossDB: Database<BossInfo, TextWithMap> = new Database("boss", _BossSource as ISource<BossInfo, TextWithMap>)

export interface IItem {
  id: number
}

export interface ISource<D, T> {
  count: number
  data: D[]
  text: Record<Lang, T>
}

export interface IWeaponDB extends ISource<WeaponInfo, Text> {}
export interface IGraceDB extends ISource<GraceInfo, TextWithMap> {}
export interface IBossDB extends ISource<BossInfo, TextWithMap> {}

// {"id":110000,"icon_id":0,"type":33,"path":"icons/icon_00000.png"}
export interface WeaponInfo {
  id: number
  icon_id: number
  type: number
  path: string
}

// {"id":300000,"map_id":61002,"eventflag_id":73000,"block":73,"offset":2875,"bit_mask":128}
export interface GraceInfo {
  id: number
  map_id: number
  eventflag_id: number
  block: number
  offset: number
  bit_mask: number
}

// {"id":10000800,"map_text_id":10000,"eventflag_id":10000800,"block":10000,"offset":1383475,"bit_mask":128}
export interface BossInfo {
  id: number
  map_text_id: number
  eventflag_id: number
  block: number
  offset: number
  bit_mask: number
}

export interface Text {
  name: Record<number, string | null>
}

export interface TextWithMap extends Text {
  map_name: Record<number, string | null>
}
