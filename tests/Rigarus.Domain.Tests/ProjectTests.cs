using Rigarus.Domain;

namespace Rigarus.Domain.Tests;

public sealed class ProjectTests
{
    [Fact]
    public void PreservesIdentifierSpellingAndLeadingZeroes()
    {
        var project = new Project("  00042  ", "  S-007  ", "  Example Hill  ");

        Assert.Equal("00042", project.JobNumber);
        Assert.Equal("S-007", project.SiteId);
        Assert.Equal("Example Hill", project.SiteName);
        Assert.Empty(project.WorkItems);
    }

    [Theory]
    [InlineData(null, "S-001", "Example Hill", "jobNumber")]
    [InlineData("  ", "S-001", "Example Hill", "jobNumber")]
    [InlineData("JOB\0-001", "S-001", "Example Hill", "jobNumber")]
    [InlineData("JOB-001", "", "Example Hill", "siteId")]
    [InlineData("JOB-001", "S-001", "\t", "siteName")]
    public void RejectsInvalidProjectFields(string? jobNumber, string siteId, string siteName, string invalidField)
    {
        var error = Assert.ThrowsAny<ArgumentException>(() => new Project(jobNumber!, siteId, siteName));

        Assert.Equal(invalidField, error.ParamName);
    }

    [Fact]
    public void KeepsIndependentEstimatesForCivilAndTowerWork()
    {
        var project = new Project("JOB-001", "S-001", "Example Hill");
        project.AddWorkItem(WorkItemType.Civil, requiredCrewCount: 2, estimatedHalfDays: 1);
        project.AddWorkItem(WorkItemType.Tower, requiredCrewCount: 1, estimatedHalfDays: 4);

        Assert.Collection(project.WorkItems,
            civil => Assert.Equal((WorkItemType.Civil, 2, 1), (civil.Type, civil.RequiredCrewCount, civil.EstimatedHalfDays)),
            tower => Assert.Equal((WorkItemType.Tower, 1, 4), (tower.Type, tower.RequiredCrewCount, tower.EstimatedHalfDays)));
    }

    [Theory]
    [InlineData((WorkItemType)0, 1, 1, "type")]
    [InlineData(WorkItemType.Civil, 0, 1, "requiredCrewCount")]
    [InlineData(WorkItemType.Civil, -1, 1, "requiredCrewCount")]
    [InlineData(WorkItemType.Tower, 1, 0, "estimatedHalfDays")]
    [InlineData(WorkItemType.Tower, 1, -1, "estimatedHalfDays")]
    public void RejectsInvalidWorkItemWithoutAddingIt(WorkItemType type, int crews, int halfDays, string invalidField)
    {
        var project = new Project("JOB-001", "S-001", "Example Hill");
        var valid = project.AddWorkItem(WorkItemType.Small, 1, 1);

        var error = Assert.Throws<ArgumentOutOfRangeException>(() => project.AddWorkItem(type, crews, halfDays));

        Assert.Equal(invalidField, error.ParamName);
        Assert.Same(valid, Assert.Single(project.WorkItems));
    }
}
