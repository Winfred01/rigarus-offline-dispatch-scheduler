using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Rigarus.Application;
using Rigarus.Domain;

namespace Rigarus.Infrastructure;

public sealed class SqliteDemoProjectStore(LocalStoragePaths paths) : IDemoProjectStore
{
    private const int SampleId = 1;

    public void Initialize()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(paths.DatabasePath)!);
        using var database = CreateContext();
        database.Database.OpenConnection();
        using var command = database.Database.GetDbConnection().CreateCommand();
        command.CommandText = "PRAGMA journal_mode = WAL;";
        if (!string.Equals(command.ExecuteScalar() as string, "wal", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("SQLite could not enable WAL mode.");
        }

        database.Database.Migrate();
    }

    public DemoProject Read()
    {
        using var database = CreateContext();
        return database.DemoProjects.AsNoTracking().Single(project => project.Id == SampleId);
    }

    public void Save(DemoProject project)
    {
        using var database = CreateContext();
        database.Attach(project).Property(item => item.Note).IsModified = true;
        database.SaveChanges();
    }

    internal DispatchDbContext CreateContext()
    {
        var connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = paths.DatabasePath,
            ForeignKeys = true,
            DefaultTimeout = 5,
            Pooling = false
        };

        var options = new DbContextOptionsBuilder<DispatchDbContext>()
            .UseSqlite(connectionString.ToString())
            .Options;

        return new DispatchDbContext(options);
    }
}
