using Microsoft.Data.Sqlite;
using Rigarus.Application;
using Rigarus.Domain;

namespace Rigarus.Infrastructure.Tests;

public sealed class SqliteDemoProjectStoreTests : IDisposable
{
    private readonly string root = Path.Combine(Path.GetTempPath(), "rigarus-m0-tests", Guid.NewGuid().ToString("N"));

    [Fact]
    public void MigratesAnEmptyDirectoryAndSeedsExactlyOneSyntheticProject()
    {
        var paths = new LocalStoragePaths(root);
        var store = new SqliteDemoProjectStore(paths);
        store.Initialize();
        store.Initialize();

        Assert.True(File.Exists(paths.DatabasePath));
        Assert.Equal("DEMO-001", store.Read().JobNumber);
        Assert.Equal("wal", Scalar("PRAGMA journal_mode;"));
        Assert.Equal(1L, Scalar("SELECT count(*) FROM DemoProjects;"));
        Assert.Equal(1L, Scalar("SELECT count(*) FROM __EFMigrationsHistory;"));
    }

    [Fact]
    public void ReopeningAfterSavePreservesTheNoteAndDoesNotReseed()
    {
        var paths = new LocalStoragePaths(root);
        var firstStore = new SqliteDemoProjectStore(paths);
        firstStore.Initialize();
        new DemoWorkspace(firstStore).SaveNote("Persisted across reopen");

        var reopened = new SqliteDemoProjectStore(paths);
        reopened.Initialize();

        Assert.Equal("Persisted across reopen", reopened.Read().Note);
        Assert.Equal(1L, Scalar("SELECT count(*) FROM DemoProjects;"));
    }

    [Fact]
    public void SqliteRejectsDuplicateJobNumberAndKeepsExistingRow()
    {
        var store = new SqliteDemoProjectStore(new LocalStoragePaths(root));
        store.Initialize();

        var error = Assert.Throws<SqliteException>(() =>
            Scalar("INSERT INTO DemoProjects (Id, JobNumber, SiteName, Note) VALUES (2, 'DEMO-001', 'Other', '');"));

        Assert.Equal(19, error.SqliteErrorCode);
        Assert.Equal(1L, Scalar("SELECT count(*) FROM DemoProjects;"));
    }

    [Fact]
    public void SqliteRejectsOversizeNoteAndKeepsExistingValue()
    {
        var store = new SqliteDemoProjectStore(new LocalStoragePaths(root));
        store.Initialize();
        var original = store.Read().Note;

        var error = Assert.Throws<SqliteException>(() =>
            Scalar($"UPDATE DemoProjects SET Note = printf('%0{DemoProject.MaximumNoteLength + 1}d', 0);"));

        Assert.Equal(19, error.SqliteErrorCode);
        Assert.Equal(original, store.Read().Note);
    }

    private object? Scalar(string sql)
    {
        var connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = new LocalStoragePaths(root).DatabasePath,
            Mode = SqliteOpenMode.ReadWrite,
            Pooling = false
        };
        using var connection = new SqliteConnection(connectionString.ToString());
        connection.Open();
        using var command = connection.CreateCommand();
        command.CommandText = sql;
        return command.ExecuteScalar();
    }

    public void Dispose()
    {
        if (Directory.Exists(root))
        {
            Directory.Delete(root, recursive: true);
        }
    }
}
