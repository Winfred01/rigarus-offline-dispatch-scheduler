using System.ComponentModel;
using System.Runtime.CompilerServices;
using Rigarus.Application;
using Rigarus.Domain;
using Rigarus.Infrastructure;

namespace Rigarus.Desktop;

internal sealed class ProjectMasterViewModel(ProjectCatalog catalog, LocalDiagnosticLog log) : INotifyPropertyChanged
{
    private ProjectSummary? selectedProject;
    private bool hasLoaded;

    public event PropertyChangedEventHandler? PropertyChanged;

    public string SearchText { get; set; } = "";
    public IReadOnlyList<ProjectSummary> Rows { get; private set; } = [];
    public Project? Detail { get; private set; }
    public string ResultsText { get; private set; } = "";
    public string EmptyText { get; private set; } = "";

    public ProjectSummary? SelectedProject
    {
        get => selectedProject;
        set
        {
            if (Equals(selectedProject, value))
            {
                return;
            }

            selectedProject = value;
            Notify();
            ReadDetail();
        }
    }

    public void Open()
    {
        if (!hasLoaded)
        {
            Search();
        }
    }

    public void Search() => Refresh(SelectedProject?.Id);

    public ProjectEditorViewModel NewProject() => new(catalog, log, null);

    public ProjectEditorViewModel? EditProject() =>
        Detail is { } project ? new ProjectEditorViewModel(catalog, log, project) : null;

    public void AfterSave(int id) => Refresh(id, revealSavedProject: true);

    private void Refresh(int? selectedId, bool revealSavedProject = false)
    {
        try
        {
            var term = SearchText.Trim();
            var rows = catalog.Search(term);
            if (revealSavedProject && term.Length > 0 && !rows.Any(project => project.Id == selectedId))
            {
                rows = catalog.Search("");
                SearchText = term = "";
                Notify(nameof(SearchText));
            }

            hasLoaded = true;
            ResultsText = rows.Count == 1 ? "1 project" : $"{rows.Count} projects";
            EmptyText = rows.Count > 0 ? "" :
                term.Length > 0 ? "No projects match your search." : "No projects yet. Create a project to start the backlog.";
            Rows = rows;
            Notify(nameof(Rows));
            selectedProject = rows.FirstOrDefault(project => project.Id == selectedId) ?? rows.FirstOrDefault();
            Notify(nameof(SelectedProject));
            ReadDetail();
        }
        catch (Exception error) when (MainWindowViewModel.IsStorageError(error))
        {
            log.WriteFailure("search-projects", error);
            ResultsText = "Could not load projects. Try Search again.";
            EmptyText = "";
        }

        Notify(nameof(ResultsText));
        Notify(nameof(EmptyText));
    }

    private void ReadDetail()
    {
        try
        {
            Detail = selectedProject is null ? null : catalog.Find(selectedProject.Id);
        }
        catch (Exception error) when (MainWindowViewModel.IsStorageError(error))
        {
            log.WriteFailure("read-project", error);
            Detail = null;
            ResultsText = "Could not open this project. Try Search again.";
            Notify(nameof(ResultsText));
        }

        Notify(nameof(Detail));
    }

    private void Notify([CallerMemberName] string? property = null) =>
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(property));
}
