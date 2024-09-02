
// https://github.com/CyberGiant7/Elden-Ring-Automatic-Checklist/blob/main/assets/js/script.js

use std::io::Read;

use anyhow::Result;
use byteorder::{ByteOrder, LE};

#[derive(Debug)]
struct Header {
  // offset: 0x00
  magic: [u8; 4], // "BND4"
  _unused: [u8; 5],
  big_endian: bool, // u8
  bit_big_endian: bool, // u8
  _unused2: [u8; 1],
  file_count: u32,
  // offset: 0x10
  header_size: u64,
  version: String, // [u8; 8], ascii
  // offset: 0x20
  file_header_size: u64,
  _unused3: [u8; 8],
  // offset: 0x30
  unicode: bool, // u8
  raw_format: u8,
  extended: u8,
  _unused4: [u8; 13],
  // offset: 0x40
}

impl Header {
  const SIZE: usize = 0x40;

  pub fn new() -> Self {
    Self {
      magic: b"BND4".clone(),
      _unused: [0; 5],
      big_endian: false,
      bit_big_endian: true,
      _unused2: [0; 1],
      file_count: 0,
      header_size: Self::SIZE as u64,
      version: String::new(),
      file_header_size: 0,
      _unused3: [0; 8],
      unicode: true,
      raw_format: 0,
      extended: 0,
      _unused4: [0; 13],
    }
  }

  pub fn from_bytes(data: &[u8]) -> Self {
    let mut header = Self::new();
    header.magic.copy_from_slice(&data[0..4]);
    header._unused.copy_from_slice(&data[4..9]);
    header.big_endian = data[9] != 0;
    header.bit_big_endian = data[10] != 0;
    header._unused2.copy_from_slice(&data[11..12]);
    header.file_count = LE::read_u32(&data[12..16]);
    header.header_size = LE::read_u64(&data[16..24]);
    header.version = String::from_utf8_lossy(&data[24..32]).to_string();
    header.file_header_size = LE::read_u64(&data[32..40]);
    header._unused3.copy_from_slice(&data[40..48]);
    header.unicode = data[48] != 0;
    header.raw_format = data[49];
    header.extended = data[50];
    header._unused4.copy_from_slice(&data[51..64]);
    header
  }

  pub fn to_bytes(&self) -> Vec<u8> {
    let mut data = Vec::with_capacity(Self::SIZE);
    data.extend_from_slice(&self.magic);
    data.extend_from_slice(&self._unused);
    data.push(self.big_endian as u8);
    data.push(self.bit_big_endian as u8);
    data.extend_from_slice(&self._unused2);
    data.extend_from_slice(&self.file_count.to_le_bytes());
    data.extend_from_slice(&self.header_size.to_le_bytes());
    let mut version = self.version.as_bytes().to_vec();
    version.resize(8, 0x30);
    data.extend_from_slice(&version);
    data.extend_from_slice(&self.file_header_size.to_le_bytes());
    data.extend_from_slice(&self._unused3);
    data.push(self.unicode as u8);
    data.push(self.raw_format);
    data.push(self.extended);
    data.extend_from_slice(&self._unused4);
    data
  }
}

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

  fn save_to_memory(&self) -> Vec<u8> {
    let mut data = Vec::with_capacity(Self::HEADER_LEN + Self::SLOT_COUNT * (Self::SLOT_CRC_LEN + Self::SLOT_LEN) + Self::SLOT_CRC_LEN + Self::SLOT_BASE_LEN + Self::TAIL_LEN);
    data.extend_from_slice(&self.header);
    for i in 0..Self::SLOT_COUNT {
      let slot = &self.data[i];
      let crc = hex_digest(slot);
      data.extend_from_slice(&hex::decode(crc).unwrap());
      data.extend_from_slice(slot);
    }
    let base = &self.base;
    let crc = hex_digest(base);
    data.extend_from_slice(&hex::decode(crc).unwrap());
    data.extend_from_slice(base);
    data.extend_from_slice(&self.tail);
    data
  }

  fn parse_header(&self) -> Header {
    Header::from_bytes(&self.header)
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
  let data_out = save.save_to_memory();
  assert_eq!(data, data_out);
  let header = save.parse_header();
  println!("header: {:?}", header);
  println!("steam_id: {}", save.get_steam_id());
  println!("names: {:?}", save.get_names());
  Ok(())
}
