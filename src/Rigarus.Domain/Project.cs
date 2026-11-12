namespace Rigarus.Domain;

public sealed class Project
{
    private readonly List<WorkItem> workItems = [];

    public Project(string jobNumber, string siteId, string siteName) =>
        (JobNumber, SiteId, SiteName) = ValidateDetails(jobNumber, siteId, siteName);

    public int Id { get; private set; }
    public string JobNumber { get; private set; }
    public string SiteId { get; private set; }
    public string SiteName { get; private set; }
    public IReadOnlyCollection<WorkItem> WorkItems => workItems.AsReadOnly();

    public void ChangeDetails(string jobNumber, string siteId, string siteName) =>
        (JobNumber, SiteId, SiteName) = ValidateDetails(jobNumber, siteId, siteName);

    public WorkItem AddWorkItem(WorkItemType type, int requiredCrewCount, int estimatedHalfDays)
    {
        var workItem = new WorkItem(type, requiredCrewCount, estimatedHalfDays);
        workItems.Add(workItem);
        return workItem;
    }

    private static (string JobNumber, string SiteId, string SiteName) ValidateDetails(string jobNumber, string siteId, string siteName) =>
        (RequireText(jobNumber, nameof(jobNumber)), RequireText(siteId, nameof(siteId)), RequireText(siteName, nameof(siteName)));

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
