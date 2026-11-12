using Rigarus.Domain;

namespace Rigarus.Domain.Tests;

public sealed class DemoProjectTests
{
    [Theory]
    [InlineData("")]
    [InlineData("Synthetic note")]
    public void ChangesNote(string note)
    {
        var project = new DemoProject(1, "DEMO-001", "Fictional site", "Original");
        project.ChangeNote(note);

        Assert.Equal(note, project.Note);
    }

    [Fact]
    public void AcceptsNoteAtMaximumLength()
    {
        var note = new string('x', DemoProject.MaximumNoteLength);
        var project = new DemoProject(1, "DEMO-001", "Fictional site", note);

        Assert.Equal(note, project.Note);
    }

    [Fact]
    public void RejectsLongNoteWithoutReplacingPreviousValue()
    {
        var project = new DemoProject(1, "DEMO-001", "Fictional site", "Original");

        Assert.Throws<ArgumentException>(() => project.ChangeNote(new string('x', DemoProject.MaximumNoteLength + 1)));
        Assert.Equal("Original", project.Note);
    }
}
