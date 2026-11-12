using Rigarus.Application;
using Rigarus.Domain;

namespace Rigarus.Infrastructure.Tests;

public sealed class ProjectCatalogTests : IDisposable
{
    private readonly DirectoryInfo root = Directory.CreateTempSubdirectory("rigarus-projects-");

    [Fact]
    public void CreatesAndEditsAnUnscheduledProjectAndRetainsWorkItemIds()
    {
        var catalog = Initialize();
        var id = catalog.Create(Draft("JOB-001"));
        Assert.Empty(Assert.IsType<Project>(catalog.Find(id)).WorkItems);
        Assert.Equal(0, Assert.Single(catalog.Search("")).WorkItemCount);

        Assert.True(catalog.Edit(id, Draft("JOB-001", "Example Ridge",
            new WorkItemDraft(null, WorkItemType.Civil, 2, 1),
            new WorkItemDraft(null, WorkItemType.Tower, 1, 6))));

        var firstRead = Assert.IsType<Project>(Reopen().Find(id));
        var civil = Assert.Single(firstRead.WorkItems, item => item.Type == WorkItemType.Civil);
        var tower = Assert.Single(firstRead.WorkItems, item => item.Type == WorkItemType.Tower);

        Assert.True(catalog.Edit(id, Draft("JOB-001A", "Example Summit",
            new WorkItemDraft(civil.Id, WorkItemType.Civil, 3, 4))));

        var reopened = Reopen();
        var summary = Assert.Single(reopened.Search("job-001a"));
        Assert.Equal((id, "Example Summit", 2), (summary.Id, summary.SiteName, summary.WorkItemCount));
        var detail = Assert.IsType<Project>(reopened.Find(id));
        var edited = Assert.Single(detail.WorkItems, item => item.Id == civil.Id);
        Assert.Equal((3, 4), (edited.RequiredCrewCount, edited.EstimatedHalfDays));
        Assert.Equal(6, Assert.Single(detail.WorkItems, item => item.Id == tower.Id).EstimatedHalfDays);
    }

    [Fact]
    public void DuplicateCreateAndEditLeaveBothProjectsAndTheirItemsIntact()
    {
        var catalog = Initialize();
        var first = catalog.Create(Draft("JOB-001", "Original Site"));
        var second = catalog.Create(Draft("JOB-002", "Second Site", new WorkItemDraft(null, WorkItemType.Civil, 2, 5)));
        var before = Assert.IsType<Project>(catalog.Find(second));
        var workItemId = Assert.Single(before.WorkItems).Id;

        Assert.Throws<DuplicateJobNumberException>(() =>
            catalog.Create(Draft(" job-001 ", "Duplicate Site", new WorkItemDraft(null, WorkItemType.Small, 1, 1))));
        Assert.Throws<DuplicateJobNumberException>(() =>
            catalog.Edit(second, Draft("job-001", "Changed Site",
                new WorkItemDraft(workItemId, WorkItemType.Civil, 5, 10),
                new WorkItemDraft(null, WorkItemType.Tower, 1, 1))));

        var reopened = Reopen();
        Assert.Equal(2, reopened.Search("").Count);
        Assert.Equal("Original Site", Assert.IsType<Project>(reopened.Find(first)).SiteName);
        var saved = Assert.IsType<Project>(reopened.Find(second));
        Assert.Equal(("JOB-002", "Second Site"), (saved.JobNumber, saved.SiteName));
        var item = Assert.Single(saved.WorkItems);
        Assert.Equal((workItemId, 2, 5), (item.Id, item.RequiredCrewCount, item.EstimatedHalfDays));
    }

    [Fact]
    public void InvalidEditDoesNotPersistAnyChanges()
    {
        var catalog = Initialize();
        var id = catalog.Create(Draft("JOB-001", "Original Site"));

        Assert.Throws<ArgumentException>(() =>
            catalog.Edit(id, Draft("JOB-001", "Changed Site",
                new WorkItemDraft(null, WorkItemType.Tower, 1, 1),
                new WorkItemDraft(999, WorkItemType.Civil, 1, 2))));

        var reopened = Assert.IsType<Project>(Reopen().Find(id));
        Assert.Equal("Original Site", reopened.SiteName);
        Assert.Empty(reopened.WorkItems);
        Assert.False(catalog.Edit(0, Draft("JOB-002")));
    }

    [Fact]
    public void SearchesOverOneHundredProjectsByEachFieldAndTreatsWildcardsAsText()
    {
        var catalog = Initialize();
        for (var number = 1; number <= 120; number++)
        {
            catalog.Create(new ProjectDraft($"JOB-{number:000}", $"SITE-{number:000}", $"Synthetic Site {number:000}", []));
        }
        var special = catalog.Create(new ProjectDraft("JOB-121", "SITE-121", "Synthetic %_\\ Site", []));

        var reopened = Reopen();
        Assert.Equal(121, reopened.Search("").Count);
        Assert.Equal("JOB-120", Assert.Single(reopened.Search(" job-120 ")).JobNumber);
        Assert.Equal("JOB-119", Assert.Single(reopened.Search("site-119")).JobNumber);
        Assert.Equal("JOB-118", Assert.Single(reopened.Search("synthetic site 118")).JobNumber);
        Assert.Equal(special, Assert.Single(reopened.Search("%")).Id);
        Assert.Equal(special, Assert.Single(reopened.Search("_")).Id);
        Assert.Equal(special, Assert.Single(reopened.Search("\\")).Id);
        Assert.Empty(reopened.Search("unmatched site"));
    }

    private ProjectCatalog Initialize()
    {
        new SqliteDemoProjectStore(new LocalStoragePaths(root.FullName)).Initialize();
        return Reopen();
    }

    private ProjectCatalog Reopen() => new(new SqliteProjectRepository(new LocalStoragePaths(root.FullName)));

    private static ProjectDraft Draft(string jobNumber, string name = "Example Site", params WorkItemDraft[] workItems) =>
        new(jobNumber, "SITE-001", name, workItems);

    public void Dispose() => root.Delete(recursive: true);
}
