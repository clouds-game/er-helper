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

  public static IntPtr LoadOodle(int version = 6) {
    Console.WriteLine($"Loading Oodle {version}");
    var ptr = NativeLibrary.LoadLibrary($"oo2core_{version}_win64");
    if (ptr != IntPtr.Zero) {
      var oodleType = typeof(SoulsFormats.Oodle);
      var fieldName = version switch {
        6 => "Oodle6Ptr",
        8 => "Oodle8Ptr",
        _ => null,
      };
      if (fieldName == null) {
        Console.WriteLine($"Invalid Oodle version {version}");
        return ptr;
      }
      var oodle6PtrField = oodleType.GetField(fieldName, System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic);
      if (oodle6PtrField == null) {
        Console.WriteLine($"Could not find field {fieldName} in {oodleType}");
      }
      oodle6PtrField?.SetValue(null, ptr);
      Console.WriteLine($"Oodle {version} loaded, {new SoulsFormats.Oodle().GetOodlePtr()}");
    }
    return ptr;
  }
}

public class Format<T> where T : SoulsFormats.SoulsFile<T>, new() {
  public static T OpenInMemory(byte[] bytes)  {
    return SoulsFormats.SoulsFile<T>.Read(bytes);
  }

  public static T OpenFile(string path) {
    return SoulsFormats.SoulsFile<T>.Read(path);
  }
}

public class NativeLibrary {
  public static void AddToPath(params string[] paths) {
    _search_paths = [
      .. paths,
      .. SearchPaths.Where(it => !paths.Contains(it)),
    ];
  }

  public static IntPtr LoadLibrary(string path) {
    if (Libraries.TryGetValue(path, out IntPtr handle)) {
      return handle;
    }
    if (System.Runtime.InteropServices.NativeLibrary.TryLoad(path, out handle)) {
      Libraries[path] = handle;
      return handle;
    }
    string? fullPath = FindLibrary(path);
    if (fullPath != null) {
      if (System.Runtime.InteropServices.NativeLibrary.TryLoad(fullPath, out handle)) {
        Libraries[path] = handle;
        return handle;
      }
    }
    return IntPtr.Zero;
  }

  public static void FreeLibrary(IntPtr handle) {
    foreach (var entry in Libraries) {
      if (entry.Value == handle) {
        Libraries.Remove(entry.Key);
        break;
      }
    }
    System.Runtime.InteropServices.NativeLibrary.Free(handle);
  }

  public static string? FindLibrary(string name) {
    var candidates = new List<string> {name};
    if (IsMacOS) {
      candidates.Add($"{name}.dylib");
      candidates.Add($"lib{name}.dylib");
    }
    if (IsLinux || IsMacOS) {
      candidates.Add($"{name}.so");
      candidates.Add($"lib{name}.so");
    }
    if (IsWindows) {
      candidates.Add($"{name}.dll");
    }
    foreach (var path in SearchPaths) {
      foreach (var candidate in candidates) {
        var file = Path.Combine(path, candidate);
        if (File.Exists(file)) {
          return file;
        }
      }
    }
    return null;
  }

  static readonly Dictionary<string, IntPtr> Libraries = [];
  static private string[] _search_paths = [];

  static readonly bool IsLinux = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Linux);
  static readonly bool IsWindows = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows);
  static readonly bool IsMacOS = System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.OSX);
  static string[] SearchPaths {
    get {
      if (_search_paths.Length == 0) {

        var paths = new List<string>();
        paths.AddRange(Environment.GetEnvironmentVariable("PATH")?.Split(Path.PathSeparator) ?? []);
        paths.AddRange(Environment.GetEnvironmentVariable("LD_LIBRARY_PATH")?.Split(Path.PathSeparator) ?? []);
        paths.AddRange(Environment.GetEnvironmentVariable("DYLD_LIBRARY_PATH")?.Split(Path.PathSeparator) ?? []);

        if (IsLinux || IsMacOS) {
            paths.Add("/usr/lib");
            paths.Add("/lib");
        }
        if (IsWindows) {
            paths.Add("C:/Windows/System32");
        }

        _search_paths = paths.Where(i => !string.IsNullOrEmpty(i)).ToArray();
      }
      return _search_paths;
    }
  }
}
