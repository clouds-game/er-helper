using System.Security.Cryptography;

namespace UnpackHelper;

public class Helper {
  public static readonly string OutputDir = Path.GetDirectoryName(System.Reflection.Assembly.GetExecutingAssembly().Location)!;

  public static string GetKey(SoulsFormats.BHD5.Game GameName, string KeyName) {
    var dictionary = GameName switch {
      SoulsFormats.BHD5.Game.DarkSouls3 => UXM.ArchiveKeys.DarkSouls3Keys,
      SoulsFormats.BHD5.Game.EldenRing => UXM.ArchiveKeys.EldenRingKeys,
      _ => throw new ArgumentException("Game not supported", nameof(GameName)),
    };
    dictionary.TryGetValue(KeyName, out string? result);
    if (result == null) {
      throw new ArgumentException($"Key {KeyName} not found", nameof(KeyName));
    }
    // var base64 = string.Concat(result.Split('\n').Where(s => !s.Trim().StartsWith("--")).ToList());
    // return Convert.FromBase64String(base64);
    return result;
  }

  public static Dictionary<ulong, string> GetDictionary(SoulsFormats.BHD5.Game game, string? path = null) {
    path ??= game switch {
      SoulsFormats.BHD5.Game.DarkSouls1 => $"{OutputDir}/res/DarkSoulsDictionary.txt",
      SoulsFormats.BHD5.Game.DarkSouls2 => $"{OutputDir}/res/DarkSouls2Dictionary.txt",
      SoulsFormats.BHD5.Game.DarkSouls3 => $"{OutputDir}/res/DarkSouls3Dictionary.txt",
      SoulsFormats.BHD5.Game.EldenRing => $"{OutputDir}/res/EldenRingDictionary.txt",
      _ => throw new ArgumentException("Game not supported", nameof(game)),
    };
    string content = File.ReadAllText(path);
    return new UXM.ArchiveDictionary(content, game).hashes;
  }

  public static SoulsFormats.BHD5 OpenHeader(SoulsFormats.BHD5.Game game, string path, string? encrypted=null) {
    SoulsFormats.BHD5 bhd;
    if (encrypted != null) {
      using MemoryStream bhdStream = UXM.CryptographyUtility.DecryptRsa(path, encrypted);
      bhd = SoulsFormats.BHD5.Read(bhdStream, game);
    } else {
      using FileStream bhdStream = File.OpenRead(path);
      bhd = SoulsFormats.BHD5.Read(bhdStream, game);
    }
    return bhd;
  }


  public static void Unpack() {
    Console.WriteLine("Unpacking...");
  }
}
