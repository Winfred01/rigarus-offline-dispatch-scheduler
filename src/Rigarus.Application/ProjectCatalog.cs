using Rigarus.Domain;

namespace Rigarus.Application;

public sealed class ProjectCatalog(IProjectRepository repository)
{
    public IReadOnlyList<ProjectSummary> Search(string term) => repository.Search(term.Trim());

    public Project? Find(int id) => repository.Find(id);

    public int Create(ProjectDraft draft)
    {
        var project = new Project(draft.JobNumber, draft.SiteId, draft.SiteName);
        ApplyWorkItems(project, draft.WorkItems);
        return repository.Add(project);
    }

    public bool Edit(int id, ProjectDraft draft) => repository.Edit(id, project =>
    {
        project.ChangeDetails(draft.JobNumber, draft.SiteId, draft.SiteName);
        ApplyWorkItems(project, draft.WorkItems);
    });

    private static void ApplyWorkItems(Project project, IReadOnlyList<WorkItemDraft> drafts)
    {
        var existing = project.WorkItems.ToDictionary(item => item.Id);
        foreach (var draft in drafts)
        {
            if (draft.Id is null)
            {
                project.AddWorkItem(draft.Type, draft.RequiredCrewCount, draft.EstimatedHalfDays);
            }
            else if (existing.Remove(draft.Id.Value, out var item))
            {
                item.ChangeRequirements(draft.Type, draft.RequiredCrewCount, draft.EstimatedHalfDays);
            }
            else
            {
                throw new ArgumentException("A work item is repeated or does not belong to this project.", nameof(drafts));
            }
        }
    }
}
