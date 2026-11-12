namespace Rigarus.Application;

public sealed class DuplicateJobNumberException(Exception innerException)
    : Exception("A project with this Job # already exists.", innerException);
