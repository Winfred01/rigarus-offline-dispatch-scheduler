namespace Rigarus.Domain;

public sealed class DemoProject(int id, string jobNumber, string siteName, string note)
{
    public const int MaximumNoteLength = 200;

    public int Id { get; private set; } = id;
    public string JobNumber { get; private set; } = jobNumber;
    public string SiteName { get; private set; } = siteName;
    public string Note { get; private set; } = ValidateNote(note);

    public void ChangeNote(string note) => Note = ValidateNote(note);

    private static string ValidateNote(string note)
    {
        ArgumentNullException.ThrowIfNull(note);
        if (note.Length > MaximumNoteLength)
        {
            throw new ArgumentException($"The demo note must be {MaximumNoteLength} characters or fewer.", nameof(note));
        }

        return note;
    }
}
