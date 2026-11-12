# Claude/hooks/limit-wake.ps1 -TargetPid <claude process> -Text "<message>"
# Types a message plus Enter into the console of that process (the Windows console input buffer), so it works in any window or tab and needs no focus.
# Exit 0 = typed; 1 = could not attach or write. Used only by limit_resume.py after a usage limit; it never opens a window.
param([int]$TargetPid, [string]$Text)
$ErrorActionPreference = "Stop"
Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public static class ConWake {
  [StructLayout(LayoutKind.Explicit, Size = 20)] public struct REC {
    [FieldOffset(0)] public ushort EventType; [FieldOffset(4)] public int KeyDown; [FieldOffset(8)] public ushort Repeat;
    [FieldOffset(10)] public ushort VK; [FieldOffset(12)] public ushort Scan; [FieldOffset(14)] public char Ch; [FieldOffset(16)] public uint Ctrl; }
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool FreeConsole();
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint pid);
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] public static extern IntPtr CreateFileW(string n, uint a, uint s, IntPtr sec, uint d, uint f, IntPtr t);
  [DllImport("kernel32.dll", SetLastError=true)] public static extern bool WriteConsoleInputW(IntPtr h, REC[] b, uint n, out uint w);
  [DllImport("kernel32.dll")] public static extern bool CloseHandle(IntPtr h);
  static REC Key(char c, ushort vk, ushort scan, bool down) { REC r = new REC(); r.EventType = 1; r.KeyDown = down ? 1 : 0; r.Repeat = 1; r.VK = vk; r.Scan = scan; r.Ch = c; return r; }
  public static bool Send(uint pid, string text) {
    FreeConsole();
    if (!AttachConsole(pid)) return false;
    IntPtr h = CreateFileW("CONIN$", 0xC0000000, 3, IntPtr.Zero, 3, 0, IntPtr.Zero);
    if (h == (IntPtr)(-1)) return false;
    uint w;
    REC[] t = new REC[text.Length * 2];
    for (int i = 0; i < text.Length; i++) { t[2*i] = Key(text[i], 0, 0, true); t[2*i+1] = Key(text[i], 0, 0, false); }
    bool ok = WriteConsoleInputW(h, t, (uint)t.Length, out w);
    System.Threading.Thread.Sleep(400);
    REC[] e = new REC[] { Key('\r', 0x0D, 0x1C, true), Key('\r', 0x0D, 0x1C, false) };
    ok = ok && WriteConsoleInputW(h, e, 2, out w);
    CloseHandle(h); FreeConsole();
    return ok;
  }
}
"@
try { if ([ConWake]::Send([uint32]$TargetPid, $Text)) { exit 0 } else { exit 1 } } catch { exit 1 }
