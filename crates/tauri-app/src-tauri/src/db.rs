use std::path::Path;

use er_save_lib::api::event_flags::EventFlagsApi;
use lazy_static::lazy_static;
pub use polars::prelude as pl;
use polars::{io::SerReader as _, prelude::IntoLazy as _};
use polars_plan::plans::TypedLiteral as _;

fn csv_options() -> pl::CsvReadOptions {
  pl::CsvReadOptions::default()
    .with_has_header(true)
    .with_parse_options(
      pl::CsvParseOptions::default()
        .with_separator(b',')
        .with_quote_char(Some(b'"'))
        .with_missing_is_null(true)
        .with_comment_prefix(Some("#"))
    )
}

pub fn load_csv<P: AsRef<Path>>(path: P) -> crate::Result<pl::DataFrame> {
  let df = csv_options()
    .try_into_reader_with_file_path(Some(path.as_ref().to_path_buf()))?
    .finish()?;
  Ok(df)
}

pub fn load_csv_in_memory(bytes: &[u8]) -> crate::Result<pl::DataFrame> {
  let file = std::io::Cursor::new(bytes);
  let df = csv_options()
    .into_reader_with_file_handle(file)
    .finish()?;
  Ok(df)
}

fn setup_graces(df: pl::DataFrame) -> crate::Result<pl::DataFrame> {
  const FLAG_DIVISOR: u32 = 1000;
  const BLOCK_SIZE: u32 = 125;
  let event_map = EventFlagsApi::event_flag_map();
  let df = df.lazy()
    .with_column(pl::col("id").cast(pl::DataType::UInt32))
    .with_columns([
      (pl::col("id") / FLAG_DIVISOR.typed_lit()).cast(pl::DataType::UInt32).alias("block"),
      (pl::col("id") % FLAG_DIVISOR.typed_lit()).cast(pl::DataType::UInt32).alias("block_idx"),
    ])
    .with_column(
      pl::col("block").map(|series| {
          Ok(series.u32()?.iter().map(|i|
            i.and_then(|i| event_map.get(&i).copied())
          ).collect::<pl::Series>().into())
        }, pl::GetOutput::from_type(pl::DataType::UInt32))
        .cast(pl::DataType::UInt32)
        .alias("offset")
    )
    .with_columns([
      pl::col("offset") * BLOCK_SIZE.typed_lit() + pl::col("block_idx") % (u8::BITS as u32).typed_lit(),
      (2u8.typed_lit().pow((u8::BITS - 1).typed_lit() - pl::col("block_idx") % u8::BITS.typed_lit())).cast(pl::DataType::UInt8).alias("bit_mask"),
    ])
    .sort(["id"], Default::default())
    .collect()?;
  println!("graces: {}", df);
  Ok(df)
}

lazy_static!{
  pub static ref GRACES: pl::DataFrame = setup_graces(load_csv_in_memory(include_bytes!("../assets/graces.csv")).unwrap()).unwrap();
}

#[test]
fn test_load_csv() {
  let df = load_csv("assets/graces.csv").unwrap();
  assert_eq!(df.shape().1, 3);
  println!("graces: {:?}", GRACES.shape());
}
