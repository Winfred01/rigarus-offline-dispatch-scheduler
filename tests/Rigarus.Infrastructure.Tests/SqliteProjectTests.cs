using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Rigarus.Domain;

namespace Rigarus.Infrastructure.Tests;

public sealed class SqliteProjectTests : IDisposable
{
    private readonly DirectoryInfo root = Directory.CreateTempSubdirectory("rigarus-i6-");

    [Fact]
    public void ReopensProjectWithDistinctWorkItemsAndStableIds()
    {
        var store = CreateInitializedStore();
        var project = new Project("JOB-001", "00017", "Example Hill");
        var civil = project.AddWorkItem(WorkItemType.Civil, 2, 1);
        var tower = project.AddWorkItem(WorkItemType.Tower, 1, 6);
        var followUp = project.AddWorkItem(WorkItemType.Tower, 1, 2);
        using (var write = store.CreateContext())
        {
            write.Projects.Add(project);
            write.SaveChanges();
        }

        using var read = store.CreateContext();
        var reopened = read.Projects.AsNoTracking().Include(item => item.WorkItems)
            .Single(item => item.JobNumber == "job-001");

        Assert.True(project.Id > 0);
        Assert.Equal(project.Id, reopened.Id);
        Assert.Equal("JOB-001", reopened.JobNumber);
        Assert.Equal("00017", reopened.SiteId);
        Assert.Equal("Example Hill", reopened.SiteName);
        Assert.Equal(3, reopened.WorkItems.Count);
        AssertWorkItem(reopened, civil, WorkItemType.Civil, 2, 1);
        AssertWorkItem(reopened, tower, WorkItemType.Tower, 1, 6);
        AssertWorkItem(reopened, followUp, WorkItemType.Tower, 1, 2);
    }

    [Fact]
    public void RejectsDuplicateJobNumberWithoutOverwritingTheOriginal()
    {
        var store = CreateInitializedStore();
        using (var write = store.CreateContext())
        {
            write.Projects.Add(new Project("JOB-001", "S-001", "Original Site"));
            write.SaveChanges();
            write.Projects.Add(new Project("  job-001  ", "S-002", "Other Site"));

            var error = Assert.Throws<DbUpdateException>(() => write.SaveChanges());
            Assert.Equal(2067, Assert.IsType<SqliteException>(error.InnerException).SqliteExtendedErrorCode);
        }

        using var read = store.CreateContext();
        var original = Assert.Single(read.Projects.AsNoTracking().Include(project => project.WorkItems));
        Assert.Equal("Original Site", original.SiteName);
        Assert.Empty(original.WorkItems);
    }

    [Theory]
    [InlineData("Unknown", 1, 1)]
    [InlineData("Civil", 0, 1)]
    [InlineData("Tower", 1, 0)]
    [InlineData("Tower", 1, 1.5)]
    public void SqliteEnforcesWorkItemChecks(string type, int crewCount, double halfDays)
    {
        var store = CreateInitializedStore();
        using var database = store.CreateContext();
        var project = new Project("JOB-001", "S-001", "Example Hill");
        database.Projects.Add(project);
        database.SaveChanges();

        var error = Assert.Throws<SqliteException>(() => database.Database.ExecuteSql($"""
            INSERT INTO WorkItems (ProjectId, Type, RequiredCrewCount, EstimatedHalfDays)
            VALUES ({project.Id}, {type}, {crewCount}, {halfDays});
            """));

        Assert.Equal(275, error.SqliteExtendedErrorCode);
        Assert.Empty(database.WorkItems);
    }

    [Fact]
    public void SqliteRejectsOrphanedWorkItemsAndProtectsTheirProject()
    {
        var store = CreateInitializedStore();
        using var database = store.CreateContext();
        var project = new Project("JOB-001", "S-001", "Example Hill");
        project.AddWorkItem(WorkItemType.Civil, 1, 1);
        database.Projects.Add(project);
        database.SaveChanges();

        var insertError = Assert.Throws<SqliteException>(() => database.Database.ExecuteSqlRaw("""
            INSERT INTO WorkItems (ProjectId, Type, RequiredCrewCount, EstimatedHalfDays)
            VALUES (0, 'Civil', 1, 1);
            """));
        Assert.Equal(787, insertError.SqliteExtendedErrorCode);

        var deleteError = Assert.Throws<SqliteException>(() =>
            database.Database.ExecuteSql($"DELETE FROM Projects WHERE Id = {project.Id};"));
        Assert.Equal(19, deleteError.SqliteErrorCode);
        Assert.Single(database.Projects);
        Assert.Single(database.WorkItems);
    }

    private SqliteDemoProjectStore CreateInitializedStore()
    {
        var store = new SqliteDemoProjectStore(new LocalStoragePaths(root.FullName));
        store.Initialize();
        return store;
    }

    private static void AssertWorkItem(Project project, WorkItem saved, WorkItemType type, int crews, int halfDays)
    {
        Assert.True(saved.Id > 0);
        var item = Assert.Single(project.WorkItems, item => item.Id == saved.Id);
        Assert.Equal((project.Id, type, crews, halfDays),
            (item.ProjectId, item.Type, item.RequiredCrewCount, item.EstimatedHalfDays));
    }

    public void Dispose() => root.Delete(recursive: true);
}
