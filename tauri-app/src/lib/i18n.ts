export const messages = {
  en: {
    ui: {
      loading: "LOADING...",
      current_runes: "Runes",
      defeated_boss: "Bosses Defeated",
      unlocked_graces: "Site of Graces",

      status: "Role Status",
      equips: "Equips",
    },
    game: {
      status: "Status",
      level: "Level",
      level_up: "Level Up",
      runes: "Rune|Runes",

      memory_slots: "Memory Slot | Memory Slots",

      main_attribute: "Main Attribute",
      attr_vigor: "Vigor",
      attr_mind: "Mind",
      attr_endurance: "Endurance",
      attr_strength: "Strength",
      attr_dexterity: "Dexterity",
      attr_intelligence: "Intelligence",
      attr_faith: "Faith",
      attr_arcane: "Arcane",

      site_of_grace: "Site of Grace | Site of Graces",
    },
    message: {
      death_times: "You died for {0} time | You died for {0} times",
      update_at: "Last update at {0}",
    },
  },
  cn: {
    ui: {
      loading: "加载中...",
      current_runes: "持有卢恩",
      defeated_boss: "Boss讨伐数",
      unlocked_graces: "已解锁赐福点",

      status: "角色状态",
      memory_slots: "记忆空格",
      equips: "装备",
    },
    game: {
      status: "状态",
      level: "等级",
      level_up: "等级提升",
      runes: "卢恩",

      memory_slots: "记忆空格",

      main_attribute: "属性",
      attr_vigor: "生命值",
      attr_mind: "精神力",
      attr_endurance: "耐力",
      attr_strength: "力气",
      attr_dexterity: "灵巧",
      attr_intelligence: "智力",
      attr_faith: "信仰",
      attr_arcane: "感应",

      site_of_grace: "赐福",
    },
    message: {
      death_times: "你一共死亡 {0} 次",
      update_at: "最后更新于 {0}",
    },
  },
  ja: {
    ui: {
      loading: "読み込み中...",
      current_runes: "ルーン",
      defeated_boss: "討伐ボス数",
      unlocked_graces: "祝福",

      status: "役職状態",
      equips: "装備",
    },
    game: {
      // https://eldenring-jp.wiki.fextralife.com/%E3%82%B9%E3%83%86%E3%83%BC%E3%82%BF%E3%82%B9
      status: "ステータス",
      level: "レベル",
      level_up: "レベルアップ",
      runes: "ルーン",

      memory_slots: "記憶スロット",

      main_attribute: "能力値",
      attr_vigor: "生命力",
      attr_mind: "精神力",
      attr_endurance: "持久力",
      attr_strength: "筋力",
      attr_dexterity: "技量",
      attr_intelligence: "知力",
      attr_faith: "信仰",
      attr_arcane: "神秘",

      site_of_grace: "祝福",
    },
    message: {
      death_times: "あなたは {0} 回死にました",
      update_at: "最終更新日： {0}",
    },
  },
} as const
