using Rigarus.Domain;

namespace Rigarus.Application;

public sealed record ProjectSummary(int Id, string JobNumber, string SiteId, string SiteName, int WorkItemCount);

public interface IProjectRepository
{
    IReadOnlyList<ProjectSummary> Search(string term);
    Project? Find(int id);
    int Add(Project project);
    bool Edit(int id, Action<Project> change);
}
