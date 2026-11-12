using Microsoft.EntityFrameworkCore;
using Rigarus.Domain;

namespace Rigarus.Infrastructure;

internal sealed class DispatchDbContext(DbContextOptions<DispatchDbContext> options) : DbContext(options)
{
    internal DbSet<DemoProject> DemoProjects => Set<DemoProject>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var project = modelBuilder.Entity<DemoProject>();
        project.ToTable("DemoProjects", table => table.HasCheckConstraint("CK_DemoProjects_NoteLength", "length(Note) <= 200"));
        project.HasKey(item => item.Id);
        project.Property(item => item.Id).ValueGeneratedNever();
        project.HasIndex(item => item.JobNumber).IsUnique();
        project.Property(item => item.Note).HasMaxLength(DemoProject.MaximumNoteLength);
    }
}
