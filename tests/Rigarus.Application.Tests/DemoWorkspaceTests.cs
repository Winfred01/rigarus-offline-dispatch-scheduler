using Rigarus.Domain;

namespace Rigarus.Application.Tests;

public sealed class DemoWorkspaceTests
{
    [Fact]
    public void OpensAndSavesTheSameSyntheticProject()
    {
        var store = new RecordingStore();
        var workspace = new DemoWorkspace(store);

        var project = workspace.OpenProject();
        Assert.Equal("DEMO-001", project.JobNumber);

        workspace.SaveNote("Edited");
        Assert.Same(project, store.SavedProject);
        Assert.Equal("Edited", store.SavedProject?.Note);
    }

    [Fact]
    public void RejectsInvalidNoteBeforeCallingSave()
    {
        var store = new RecordingStore();
        var workspace = new DemoWorkspace(store);

        Assert.Throws<ArgumentException>(() => workspace.SaveNote(new string('x', DemoProject.MaximumNoteLength + 1)));
        Assert.Null(store.SavedProject);
        Assert.Equal("Original", workspace.OpenProject().Note);
    }

    private sealed class RecordingStore : IDemoProjectStore
    {
        private readonly DemoProject project = new(1, "DEMO-001", "Fictional site", "Original");

        public DemoProject? SavedProject { get; private set; }

        public DemoProject Read() => project;

        public void Save(DemoProject project) => SavedProject = project;
    }
}
