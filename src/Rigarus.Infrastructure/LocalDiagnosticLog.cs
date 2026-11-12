namespace Rigarus.Infrastructure;

public sealed class LocalDiagnosticLog(LocalStoragePaths paths)
{
    private const long MaximumBytes = 64 * 1024;

    public void WriteFailure(string operation, Exception error)
    {
        try
        {
            Directory.CreateDirectory(paths.LogDirectory);
            var path = Path.Combine(paths.LogDirectory, "startup.log");
            var file = new FileInfo(path);
            if (file.Exists && file.Length >= MaximumBytes)
            {
                File.Move(path, Path.Combine(paths.LogDirectory, "startup.previous.log"), overwrite: true);
            }

            File.AppendAllText(path, $"{DateTimeOffset.UtcNow:O} {operation} {error.GetType().Name}{Environment.NewLine}");
        }
        catch (Exception loggingError) when (loggingError is IOException or UnauthorizedAccessException)
        {
            // Preserve the original error when the log directory is inaccessible.
        }
    }
}
