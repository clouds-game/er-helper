use er_save_lib::{save::user_data_10::Profile, Save};

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
    let mut player_infos = save.user_data_10.profile_summary.profiles.iter().map(|p| p.into()).collect::<Vec<PlayerMetaInfo>>();
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

impl MetaInfo {
  pub fn get_active(&self) -> &PlayerMetaInfo {
    &self.player_infos[self.active_slot]
  }

  pub fn get_active_name(&self) -> &str {
    &self.slot_names[self.active_slot]
  }
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PlayerMetaInfo {
  pub active: bool,
  pub name: String,
  pub level: u32,
  pub duration: u32,
  pub runes: u32,
  pub map_id: u32,
}

impl From<&Profile> for PlayerMetaInfo {
  fn from(profile: &Profile) -> Self {
    Self {
      active: false,
      name: profile.character_name.clone(),
      level: profile.level,
      duration: profile.seconds_played,
      runes: profile.runes_memory,
      map_id: u32::from_le_bytes(profile.map_id),
    }
  }
}

impl MyState {
  pub fn get_selected(&self) -> Option<String> {
    let selected = self.selected.lock().unwrap().clone();
    if selected.is_none() {
      let save = self.save.lock().unwrap();
      let Some(save) = Option::as_ref(&save) else {
        return None;
      };
      let meta_info = MetaInfo::from(save);
      Some(meta_info.get_active_name().to_string())
    } else {
      selected
    }
  }

  pub fn get_basic_info(&self) -> Result<crate::BasicInfo> {
    let save = self.save.lock().unwrap();
    let Some(save) = Option::as_ref(&save) else {
      anyhow::bail!("no save loaded");
    };
    let meta_info = MetaInfo::from(save);
    let active = meta_info.get_active();
    Ok(crate::BasicInfo {
      nickname: "miao".to_string(),
      role_name: active.name.to_string(),
      duration: active.duration as u64,
      steam_id: meta_info.steam_id.to_string(),
    })
  }

  pub fn get_player_info(&self, selected: String) -> Result<crate::BasicPlayerInfo> {
    let save = self.save.lock().unwrap();
    let Some(save) = Option::as_ref(&save) else {
      anyhow::bail!("no save loaded");
    };
    let meta_info = MetaInfo::from(save);
    let active = meta_info.get_active();
    Ok(crate::BasicPlayerInfo {
      level: active.level as _,
      rune: active.runes as _,
      boss: 0,
      place: 0,
      death: 0,
    })
  }
}
