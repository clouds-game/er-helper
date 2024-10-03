use std::collections::HashMap;

use er_save_lib::{save::{user_data_10::Profile, user_data_x::UserDataX}, Save};

use crate::{db::{BOSS, GRACES}, sync::MyState, Result};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct MetaInfo {
  pub steam_id: u64,
  pub version: u32,
  pub slot_names: Vec<String>,
  pub player_infos: Vec<PlayerMetaInfo>,
  pub active_slot: usize,
  pub slot_count: usize,
}

impl From<&Save> for MetaInfo {
  fn from(save: &Save) -> Self {
    let mut player_infos = save.user_data_10.profile_summary.profiles.iter().zip(save.user_data_x.iter()).map(|p| p.into()).collect::<Vec<PlayerMetaInfo>>();
    for (info, active) in player_infos.iter_mut().zip(save.user_data_10.profile_summary.active_profiles.iter()) {
      info.active = *active;
    }
    Self {
      steam_id: save.user_data_10.steam_id,
      version: save.user_data_10.version,
      slot_names: player_infos.iter().map(|i| i.name.clone()).collect(),
      slot_count: player_infos.iter().filter(|i| i.level > 0).count(),
      player_infos: player_infos,
      active_slot: save.user_data_10.profile_summary.active_profiles.iter().position(|&a| a).unwrap_or(0),
    }
  }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PlayerMetaInfo {
  pub active: bool,
  pub name: String,
  pub level: u32,
  pub duration: u32,
  pub runes: u32,
  pub total_runes: u32,
  pub map_id: u32,
  pub death: u32,
  pub last_grace_id: u32,
  pub boss: u32,
  pub grace: u32,

  /// in order `vigor, mind, endurance, strength, dexterity, intelligence, faith, arcane`
  pub attrs: [u32; 8],
  pub hp: [u32; 3],
  pub fp: [u32; 3],
  pub sp: [u32; 3],
}

macro_rules! check_eq {
  ($left:expr, $right:expr) => {
    {
      let (left, right) = ($left, $right);
      if left != right {
        error!("{} == {} failed with left={} right={}", stringify!($left), stringify!($right), left, right)
      }
    }
  };
}

pub struct Events {
  pub events: Vec<u8>,
  pub graces: HashMap<u32, bool>,
  pub bosses: HashMap<u32, bool>,
}

impl std::fmt::Debug for Events {
  fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
    f.debug_struct("Events").field("events", &self.events.len()).field("graces", &self.graces.len()).field("bosses", &self.bosses.len()).finish()
  }
}

impl TryFrom<&UserDataX> for Events {
  type Error = anyhow::Error;

  // #[instrument(skip(userdata))]
  fn try_from(userdata: &UserDataX) -> Result<Self> {
    let events = userdata.event_flags.clone();
    let mut graces = HashMap::new();
    for i in GRACES.data.iter() {
      let flag = events[i.offset as usize] & i.bit_mask != 0;
      graces.insert(i.id, flag);
    }
    let mut bosses = HashMap::new();
    for i in BOSS.data.iter() {
      let flag = events[i.offset as usize] & i.bit_mask != 0;
      bosses.insert(i.id, flag);
    }
    Ok(Self {
      events, graces, bosses,
    })
  }
}

impl From<(&Profile, &UserDataX)> for PlayerMetaInfo {
  fn from((profile, userdata): (&Profile, &UserDataX)) -> Self {
    check_eq!(profile.runes_memory, userdata.player_game_data.runes_memory);

    let events = Events::try_from(userdata).unwrap();
    let grace = events.graces.iter().filter(|(_, &v)| v).count() as u32;
    let boss = events.bosses.iter().filter(|(_, &v)| v).count() as u32;

    let player = &userdata.player_game_data;

    Self {
      active: false,
      name: profile.character_name.clone(),
      level: profile.level,
      duration: profile.seconds_played,
      runes: player.runes,
      total_runes: profile.runes_memory,
      map_id: u32::from_le_bytes(profile.map_id),
      death: userdata.total_deaths_count,
      last_grace_id: userdata.last_rested_grace,
      boss,
      grace,
      attrs: [player.vigor, player.mind, player.endurance, player.strength, player.dexterity, player.intelligence, player.faith, player.arcane],
      hp: [player.hp, player.max_hp, player.base_max_hp],
      fp: [player.fp, player.max_fp, player.base_max_fp],
      sp: [player.sp, player.max_sp, player.base_max_sp],

    }
  }
}

impl MyState {
  pub fn get_meta_info(&self) -> Result<MetaInfo> {
    self.get_from_cache_or_save::<MetaInfo>()
  }

  pub fn get_selected(&self) -> usize {
    let selected = self.selected.load(std::sync::atomic::Ordering::SeqCst);
    if selected == usize::MAX {
      let Ok(meta_info) = self.get_meta_info() else {
        return 0;
      };
      meta_info.active_slot
    } else {
      selected
    }
  }

  pub fn get_basic_info(&self, selected: usize) -> Result<crate::BasicInfo> {
    let meta_info = self.get_meta_info()?;
    let player_info = &meta_info.player_infos[selected];
    Ok(crate::BasicInfo {
      role_name: player_info.name.to_string(),
      duration: player_info.duration as u64,
      steam_id: meta_info.steam_id.to_string(),
      level: player_info.level as _,
      rune: player_info.runes as _,
      boss: player_info.boss as _,
      grace: player_info.grace as _,
      death: player_info.death as _,
      attrs: player_info.attrs,
      hp: player_info.hp,
      fp: player_info.fp,
      sp: player_info.sp,
    })
  }
}
