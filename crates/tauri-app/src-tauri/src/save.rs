use er_save_lib::{save::{user_data_10::Profile, user_data_x::UserDataX}, Save};

use crate::{sync::MyState, Result};

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
  pub graces: u32,
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

impl From<(&Profile, &UserDataX)> for PlayerMetaInfo {
  fn from((profile, userdata): (&Profile, &UserDataX)) -> Self {
    check_eq!(profile.runes_memory, userdata.player_game_data.runes_memory);
    Self {
      active: false,
      name: profile.character_name.clone(),
      level: profile.level,
      duration: profile.seconds_played,
      runes: userdata.player_game_data.runes,
      total_runes: profile.runes_memory,
      map_id: u32::from_le_bytes(profile.map_id),
      death: userdata.total_deaths_count,
      last_grace_id: userdata.last_rested_grace,
      boss: 0, // userdata.event_flags,
      graces: 0,
    }
  }
}

impl MyState {
  pub fn get_selected(&self) -> usize {
    let selected = self.selected.load(std::sync::atomic::Ordering::SeqCst);
    if selected == usize::MAX {
      let save = self.save.lock().unwrap();
      let Some(save) = Option::as_ref(&save) else {
        return 0;
      };
      let meta_info = MetaInfo::from(save);
      meta_info.active_slot
    } else {
      selected
    }
  }

  pub fn get_basic_info(&self, selected: usize) -> Result<crate::BasicInfo> {
    let save = self.save.lock().unwrap();
    let Some(save) = Option::as_ref(&save) else {
      anyhow::bail!("no save loaded");
    };
    let meta_info = MetaInfo::from(save);
    let player_info = &meta_info.player_infos[selected];
    Ok(crate::BasicInfo {
      nickname: "miao".to_string(),
      role_name: player_info.name.to_string(),
      duration: player_info.duration as u64,
      steam_id: meta_info.steam_id.to_string(),
    })
  }

  pub fn get_player_info(&self, selected: usize) -> Result<crate::BasicPlayerInfo> {
    let save = self.save.lock().unwrap();
    let Some(save) = Option::as_ref(&save) else {
      anyhow::bail!("no save loaded");
    };
    let meta_info = MetaInfo::from(save);
    let player_info = &meta_info.player_infos[selected];
    Ok(crate::BasicPlayerInfo {
      level: player_info.level as _,
      rune: player_info.runes as _,
      boss: player_info.boss as _,
      grace: player_info.graces as _,
      death: player_info.death as _,
    })
  }
}
