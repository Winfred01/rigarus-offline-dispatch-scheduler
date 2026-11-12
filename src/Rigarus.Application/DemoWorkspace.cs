using Rigarus.Domain;

namespace Rigarus.Application;

public sealed class DemoWorkspace(IDemoProjectStore projects)
{
    public DemoProject OpenProject() => projects.Read();

    public DemoProject SaveNote(string note)
    {
        var project = projects.Read();
        project.ChangeNote(note);
        projects.Save(project);
        return project;
    }
}
