namespace Rigarus.Domain;

public sealed class Project
{
    private readonly List<WorkItem> workItems = [];

    public Project(string jobNumber, string siteId, string siteName)
    {
        JobNumber = RequireText(jobNumber, nameof(jobNumber));
        SiteId = RequireText(siteId, nameof(siteId));
        SiteName = RequireText(siteName, nameof(siteName));
    }

    public int Id { get; private set; }
    public string JobNumber { get; }
    public string SiteId { get; }
    public string SiteName { get; }
    public IReadOnlyCollection<WorkItem> WorkItems => workItems.AsReadOnly();

    public WorkItem AddWorkItem(WorkItemType type, int requiredCrewCount, int estimatedHalfDays)
    {
        var workItem = new WorkItem(type, requiredCrewCount, estimatedHalfDays);
        workItems.Add(workItem);
        return workItem;
    }

    private static string RequireText(string value, string parameterName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value, parameterName);
        if (value.Contains('\0'))
        {
            throw new ArgumentException("The value must not contain a null character.", parameterName);
        }

        return value.Trim();
    }
}
