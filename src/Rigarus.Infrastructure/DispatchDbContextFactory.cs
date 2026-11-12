using Microsoft.EntityFrameworkCore.Design;

namespace Rigarus.Infrastructure;

internal sealed class DispatchDbContextFactory : IDesignTimeDbContextFactory<DispatchDbContext>
{
    public DispatchDbContext CreateDbContext(string[] args) =>
        new SqliteDemoProjectStore(new LocalStoragePaths(Path.Combine(Environment.CurrentDirectory, ".local", "ef-design"))).CreateContext();
}
