using System.ComponentModel;
using System.IO;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Rigarus.Application;
using Rigarus.Infrastructure;

namespace Rigarus.Desktop;

internal sealed class MainWindowViewModel(DemoWorkspace workspace, LocalDiagnosticLog log, ProjectMasterViewModel projects) : INotifyPropertyChanged
{
    private string status = "";

    public event PropertyChangedEventHandler? PropertyChanged;

    public string ProjectLabel { get; private set; } = "Sample unavailable";
    public string Note { get; set; } = "";
    public bool CanEdit { get; private set; }
    public ProjectMasterViewModel Projects => projects;

    public string Status
    {
        get => status;
        private set
        {
            status = value;
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(Status)));
        }
    }

    public void Initialize(Action initializeStorage)
    {
        try
        {
            initializeStorage();
            var project = workspace.OpenProject();
            ProjectLabel = $"{project.JobNumber}  ·  {project.SiteName}";
            Note = project.Note;
            CanEdit = true;
            Status = "Loaded from the local database.";
        }
        catch (Exception error) when (IsStorageError(error))
        {
            log.WriteFailure("open-database", error);
            Status = "The local database could not be opened. Check disk space and access, then restart the app.";
        }
    }

    public void SaveNote()
    {
        try
        {
            workspace.SaveNote(Note);
            Status = "Saved locally.";
        }
        catch (ArgumentException)
        {
            Status = "Enter a shorter demo note.";
        }
        catch (Exception error) when (IsStorageError(error))
        {
            log.WriteFailure("save-demo-note", error);
            Status = "The note could not be saved. Check disk space and access, then try again.";
        }
    }

    internal static bool IsStorageError(Exception error) =>
        error is IOException or UnauthorizedAccessException or SqliteException or DbUpdateException or InvalidOperationException;
}
