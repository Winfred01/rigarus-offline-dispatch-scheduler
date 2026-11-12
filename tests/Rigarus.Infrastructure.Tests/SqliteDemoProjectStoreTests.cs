using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using Rigarus.Application;
using Rigarus.Domain;

namespace Rigarus.Infrastructure.Tests;

public sealed class SqliteDemoProjectStoreTests : IDisposable
{
    private const string InitialMigration = "20261112045924_InitialDemo";
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
        using var database = store.CreateContext();
        Assert.Contains(InitialMigration, database.Database.GetAppliedMigrations());
        Assert.Empty(database.Database.GetPendingMigrations());
    }

    [Fact]
    public void UpgradesM0DatabaseInPlaceAndPreservesTheEditedDemoFixture()
    {
        var paths = new LocalStoragePaths(root);
        Directory.CreateDirectory(Path.GetDirectoryName(paths.DatabasePath)!);
        var store = new SqliteDemoProjectStore(paths);
        using (var legacy = store.CreateContext())
        {
            legacy.GetService<IMigrator>().Migrate(InitialMigration);
            Assert.Equal(InitialMigration, Assert.Single(legacy.Database.GetAppliedMigrations()));
        }

        const string note = "Saved in M0 before upgrading";
        new DemoWorkspace(store).SaveNote(note);
        var before = store.Read();

        store.Initialize();
        store.Initialize();
        using (var upgraded = store.CreateContext())
        {
            var applied = upgraded.Database.GetAppliedMigrations().ToArray();
            Assert.Contains(InitialMigration, applied);
            Assert.Single(applied, name => name.EndsWith("_AddProjectsAndWorkItems", StringComparison.Ordinal));
            Assert.Empty(upgraded.Database.GetPendingMigrations());
            Assert.Empty(upgraded.Projects);
            Assert.Empty(upgraded.WorkItems);

            var project = new Project("JOB-017", "S-017", "Example Hill");
            project.AddWorkItem(WorkItemType.Tower, 1, 1);
            upgraded.Projects.Add(project);
            upgraded.SaveChanges();
        }

        using var reopened = store.CreateContext();
        var fixture = Assert.Single(reopened.DemoProjects.AsNoTracking());
        Assert.Equal((before.Id, "DEMO-001", before.SiteName, note),
            (fixture.Id, fixture.JobNumber, fixture.SiteName, fixture.Note));
        Assert.Equal("JOB-017", Assert.Single(reopened.Projects.AsNoTracking()).JobNumber);
        Assert.Equal(WorkItemType.Tower, Assert.Single(reopened.WorkItems.AsNoTracking()).Type);
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
