namespace Rigarus.Infrastructure.Tests;

public sealed class LocalDiagnosticLogTests
{
    [Fact]
    public void LogsOperationAndExceptionTypeWithoutExceptionMessage()
    {
        var root = Directory.CreateTempSubdirectory("rigarus-log-");
        try
        {
            var paths = new LocalStoragePaths(root.FullName);
            new LocalDiagnosticLog(paths).WriteFailure("open-database", new IOException("sensitive example"));

            var entry = File.ReadAllText(Path.Combine(paths.LogDirectory, "startup.log"));
            Assert.Contains("open-database IOException", entry);
            Assert.DoesNotContain("sensitive example", entry);
        }
        finally
        {
            root.Delete(recursive: true);
        }
    }
}
