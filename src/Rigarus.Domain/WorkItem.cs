namespace Rigarus.Domain;

public sealed class WorkItem
{
    internal WorkItem(WorkItemType type, int requiredCrewCount, int estimatedHalfDays) =>
        ChangeRequirements(type, requiredCrewCount, estimatedHalfDays);

    public void ChangeRequirements(WorkItemType type, int requiredCrewCount, int estimatedHalfDays)
    {
        if (!Enum.IsDefined(type))
        {
            throw new ArgumentOutOfRangeException(nameof(type), type, "Choose a supported work item type.");
        }

        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(requiredCrewCount);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(estimatedHalfDays);

        Type = type;
        RequiredCrewCount = requiredCrewCount;
        EstimatedHalfDays = estimatedHalfDays;
    }

    public int Id { get; private set; }
    public int ProjectId { get; private set; }
    public WorkItemType Type { get; private set; }
    public int RequiredCrewCount { get; private set; }
    public int EstimatedHalfDays { get; private set; }
}
