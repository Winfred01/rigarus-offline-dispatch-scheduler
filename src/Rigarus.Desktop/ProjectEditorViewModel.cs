using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Globalization;
using Rigarus.Application;
using Rigarus.Domain;
using Rigarus.Infrastructure;

namespace Rigarus.Desktop;

internal sealed class ProjectEditorViewModel : INotifyPropertyChanged
{
    private readonly ProjectCatalog catalog;
    private readonly LocalDiagnosticLog log;
    private readonly int? projectId;

    public ProjectEditorViewModel(ProjectCatalog catalog, LocalDiagnosticLog log, Project? project)
    {
        this.catalog = catalog;
        this.log = log;
        projectId = project?.Id;
        JobNumber = project?.JobNumber ?? "";
        SiteId = project?.SiteId ?? "";
        SiteName = project?.SiteName ?? "";

        if (project is not null)
        {
            foreach (var item in project.WorkItems.OrderBy(item => item.Id))
            {
                WorkItems.Add(new WorkItemInput
                {
                    Id = item.Id,
                    Type = item.Type,
                    CrewCount = item.RequiredCrewCount.ToString(CultureInfo.InvariantCulture),
                    HalfDays = item.EstimatedHalfDays.ToString(CultureInfo.InvariantCulture)
                });
            }
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    public string Title => projectId is null ? "New project" : "Edit project";
    public string JobNumber { get; set; }
    public string SiteId { get; set; }
    public string SiteName { get; set; }
    public ObservableCollection<WorkItemInput> WorkItems { get; } = [];
    public WorkItemType[] WorkItemTypes { get; } = Enum.GetValues<WorkItemType>();
    public string Error { get; private set; } = "";
    public int SavedId { get; private set; }

    public void AddWorkItem() => WorkItems.Add(new WorkItemInput());

    public void RemoveDraft(WorkItemInput item)
    {
        if (item.CanRemove)
        {
            WorkItems.Remove(item);
        }
    }

    public bool TrySave()
    {
        try
        {
            var items = new List<WorkItemDraft>();
            for (var index = 0; index < WorkItems.Count; index++)
            {
                var item = WorkItems[index];
                if (!TryPositiveInteger(item.CrewCount, out var crews) || !TryPositiveInteger(item.HalfDays, out var halfDays))
                {
                    return Fail($"Work item {index + 1} needs a positive whole number for crews and estimated half-days.");
                }

                items.Add(new WorkItemDraft(item.Id, item.Type, crews, halfDays));
            }

            var draft = new ProjectDraft(JobNumber, SiteId, SiteName, items);
            if (projectId is int id)
            {
                if (!catalog.Edit(id, draft))
                {
                    return Fail("This project could not be found. Cancel and refresh the backlog.");
                }

                SavedId = id;
            }
            else
            {
                SavedId = catalog.Create(draft);
            }

            return true;
        }
        catch (DuplicateJobNumberException error)
        {
            return Fail(error.Message);
        }
        catch (ArgumentException error)
        {
            return Fail(error.ParamName switch
            {
                "jobNumber" => "Enter a valid Job #.",
                "siteId" => "Enter a valid Site ID.",
                "siteName" => "Enter a valid site name.",
                _ => "Review the work items and try again."
            });
        }
        catch (Exception error) when (MainWindowViewModel.IsStorageError(error))
        {
            log.WriteFailure("save-project", error);
            return Fail("Could not save the project. Check disk space and access, then try again.");
        }
    }

    private bool Fail(string message)
    {
        Error = message;
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Error)));
        return false;
    }

    private static bool TryPositiveInteger(string text, out int value) =>
        int.TryParse(text, NumberStyles.Integer, CultureInfo.InvariantCulture, out value) && value > 0;
}

internal sealed class WorkItemInput
{
    public int? Id { get; init; }
    public WorkItemType Type { get; set; } = WorkItemType.Small;
    public string CrewCount { get; set; } = "1";
    public string HalfDays { get; set; } = "1";
    public bool CanRemove => Id is null;
}
