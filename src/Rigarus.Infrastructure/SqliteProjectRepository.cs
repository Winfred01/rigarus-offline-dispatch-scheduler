using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Rigarus.Application;
using Rigarus.Domain;

namespace Rigarus.Infrastructure;

public sealed class SqliteProjectRepository(LocalStoragePaths paths) : IProjectRepository
{
    public IReadOnlyList<ProjectSummary> Search(string term)
    {
        using var database = DispatchDbContext.Open(paths);
        var projects = database.Projects.AsNoTracking();
        if (term.Length > 0)
        {
            var literal = term.Replace("\\", "\\\\").Replace("%", "\\%").Replace("_", "\\_");
            var pattern = $"%{literal}%";
            projects = projects.Where(project =>
                EF.Functions.Like(project.JobNumber, pattern, "\\") ||
                EF.Functions.Like(project.SiteId, pattern, "\\") ||
                EF.Functions.Like(project.SiteName, pattern, "\\"));
        }

        return projects.OrderBy(project => project.JobNumber)
            .Select(project => new ProjectSummary(project.Id, project.JobNumber, project.SiteId, project.SiteName, project.WorkItems.Count))
            .ToList();
    }

    public Project? Find(int id)
    {
        using var database = DispatchDbContext.Open(paths);
        return database.Projects.AsNoTracking().Include(project => project.WorkItems.OrderBy(item => item.Id))
            .SingleOrDefault(project => project.Id == id);
    }

    public int Add(Project project)
    {
        using var database = DispatchDbContext.Open(paths);
        database.Projects.Add(project);
        Save(database);
        return project.Id;
    }

    public bool Edit(int id, Action<Project> change)
    {
        using var database = DispatchDbContext.Open(paths);
        var project = database.Projects.Include(project => project.WorkItems).SingleOrDefault(project => project.Id == id);
        if (project is null)
        {
            return false;
        }

        change(project);
        Save(database);
        return true;
    }

    private static void Save(DispatchDbContext database)
    {
        try
        {
            database.SaveChanges();
        }
        catch (DbUpdateException error) when (error.InnerException is SqliteException { SqliteExtendedErrorCode: 2067 })
        {
            throw new DuplicateJobNumberException(error);
        }
    }
}
