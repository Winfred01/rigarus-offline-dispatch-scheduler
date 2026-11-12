using Rigarus.Domain;

namespace Rigarus.Application;

public interface IDemoProjectStore
{
    DemoProject Read();
    void Save(DemoProject project);
}
