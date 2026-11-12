namespace Rigarus.Infrastructure;

public sealed class LocalStoragePaths(string root)
{
    public string DatabasePath { get; } = Path.Combine(root, "data", "rigarus.db");
    public string LogDirectory { get; } = Path.Combine(root, "logs");

    public static LocalStoragePaths ForCurrentUser() =>
        new(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RigarusDispatch"));
}
