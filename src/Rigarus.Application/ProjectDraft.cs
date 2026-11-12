using Rigarus.Domain;

namespace Rigarus.Application;

public sealed record ProjectDraft(string JobNumber, string SiteId, string SiteName, IReadOnlyList<WorkItemDraft> WorkItems);

public sealed record WorkItemDraft(int? Id, WorkItemType Type, int RequiredCrewCount, int EstimatedHalfDays);
