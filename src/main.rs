
// https://github.com/CyberGiant7/Elden-Ring-Automatic-Checklist/blob/main/assets/js/script.js

use std::io::Read;

use anyhow::Result;
use byteorder::{ByteOrder, LE};

struct SaveFile {
  header: [u8; Self::HEADER_LEN],
  data: [Vec<u8>; Self::SLOT_COUNT],
  base: Vec<u8>, // 0x019003B0+60000h
  tail: Vec<u8>, // 0x019603B0+240020h
}

impl SaveFile {
  const HEADER_LEN: usize = 0x300;
  const SLOT_CRC_LEN: usize = 0x10;
  const SLOT_LEN: usize = 0x280000; //2621439;
  const SLOT_COUNT: usize = 10;
  const SLOT_BASE_LEN: usize = 0x60000;
  const TAIL_LEN: usize = 0x240020;

  fn new() -> Self {
    Self {
      header: [0; Self::HEADER_LEN],
      data: core::array::from_fn(|_| vec![]),
      base: vec![],
      tail: vec![],
    }
  }

  fn load_from_memory(data: &[u8]) -> Result<Self> {
    let mut save = Self::new();
    save.header.copy_from_slice(&data[..Self::HEADER_LEN]);
    let mut offset = Self::HEADER_LEN;
    let zero_crc_str = hex_digest(&vec![0; Self::SLOT_LEN]);
    println!("zero digest: {}", zero_crc_str);
    for i in 0..Self::SLOT_COUNT {
      let crc = &data[offset..offset + Self::SLOT_CRC_LEN];
      offset += Self::SLOT_CRC_LEN;
      let slot = &data[offset..offset + Self::SLOT_LEN];
      offset += Self::SLOT_LEN;
      save.data[i] = slot.to_vec();
      let str = hex_digest(slot);
      let crc_str = hex::encode(crc);
      if crc_str == str {
        if str != zero_crc_str {
          println!("Slot {} CRC: {:?}", i, str);
        }
      } else {
        println!("Slot {} (+{:x}) CRC: {:?} != {:?}", i, offset, crc_str, str);
      }
    }
    let crc = &data[offset..offset + Self::SLOT_CRC_LEN];
    offset += Self::SLOT_CRC_LEN;
    let slot = &data[offset..offset + Self::SLOT_BASE_LEN];
    offset += Self::SLOT_BASE_LEN;
    let str = hex_digest(slot);
    let crc_str = hex::encode(crc);
    assert_eq!(offset, 0x019603B0);
    if crc_str == str {
      if str != zero_crc_str {
        println!("Slot {} CRC: {:?}", "base", str);
      }
    } else {
      println!("Slot {} (+{:x}) CRC: {:?} != {:?}", "base", offset, crc_str, str);
    }
    save.base = slot.to_vec();
    save.tail = data[offset..].to_vec();
    assert_eq!(save.tail.len(), Self::TAIL_LEN);
    Ok(save)
  }

  fn get_steam_id(&self) -> u64 {
    // https://github.com/Ariescyn/EldenRing-Save-Manager/blob/101c5b26ffc89210ad9d027e0ff8aecc7371758c/hexedit.py#L181
    // f.seek(26215348)  # start address of steamID
    // steam_id = f.read(8)  # Get steamID
    // 0x4
    let id = LE::read_u64(&self.base[0x4..0xC]);
    assert_eq!(format!("{}", id).len(), 17);
    id
  }

  fn get_names(&self) -> Vec<String> {
    // https://github.com/CyberGiant7/Elden-Ring-Automatic-Checklist/blob/b81827cfeacfb120c0bf010f17c9878e6cf51c97/assets/js/script.js#L262
    // let name1 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x1901d0e, 0x1901d0e + 32)))));
    // let name2 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x1901f5a, 0x1901f5a + 32)))));
    // let name3 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x19021a6, 0x19021a6 + 32)))));
    // let name4 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x19023f2, 0x19023f2 + 32)))));
    // let name5 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x190263e, 0x190263e + 32)))));
    // let name6 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x190288a, 0x190288a + 32)))));
    // let name7 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x1902ad6, 0x1902ad6 + 32)))));
    // let name8 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x1902d22, 0x1902d22 + 32)))));
    // let name9 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x1902f6e, 0x1902f6e + 32)))));
    // let name10 = decoder.decode(new Int8Array(Array.from(new Uint16Array(file_read.slice(0x19031ba, 0x19031ba + 32)))));
    // 0x195E, 0x1BAA
    // 0x24C
    let mut names = Vec::new();
    let mut offset = 0x195E;
    for _ in 0..Self::SLOT_COUNT {
      let bytes: &[u8] = &self.base[offset..offset + 0x20];
      let name = String::from_utf16_lossy(&le_u16_slice(bytes));
      names.push(name.trim_end_matches('\0').to_string());
      offset += 0x24C;
    }
    names
  }
}

fn le_u16_slice(data: &[u8]) -> Vec<u16> {
  let mut bytes = Vec::with_capacity(data.len() / 2);
  for i in (0..data.len()).step_by(2) {
    bytes.push(LE::read_u16(&data[i..i+2]));
  }
  bytes
}

fn hex_digest(data: &[u8]) -> String {
  use md5::Digest;
  format!("{:x}", md5::Md5::digest(data))
}

fn main() -> Result<()> {
  let mut file = std::fs::File::open("/tmp/ER0000.sl2")?;
  let mut data = Vec::new(); 
  file.read_to_end(&mut data)?;
  let save = SaveFile::load_from_memory(&data)?;
  println!("steam_id: {}", save.get_steam_id());
  println!("names: {:?}", save.get_names());
  Ok(())
}
