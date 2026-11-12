using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Rigarus.Domain;

namespace Rigarus.Infrastructure;

internal sealed class DispatchDbContext(DbContextOptions<DispatchDbContext> options) : DbContext(options)
{
    internal DbSet<DemoProject> DemoProjects => Set<DemoProject>();
    internal DbSet<Project> Projects => Set<Project>();
    internal DbSet<WorkItem> WorkItems => Set<WorkItem>();

    internal static DispatchDbContext Open(LocalStoragePaths paths)
    {
        var connectionString = new SqliteConnectionStringBuilder
        {
            DataSource = paths.DatabasePath,
            ForeignKeys = true,
            DefaultTimeout = 5,
            Pooling = false
        };
        var options = new DbContextOptionsBuilder<DispatchDbContext>()
            .UseSqlite(connectionString.ToString())
            .Options;
        return new DispatchDbContext(options);
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var demo = modelBuilder.Entity<DemoProject>();
        demo.ToTable("DemoProjects", table => table.HasCheckConstraint("CK_DemoProjects_NoteLength", "length(Note) <= 200"));
        demo.HasKey(item => item.Id);
        demo.Property(item => item.Id).ValueGeneratedNever();
        demo.HasIndex(item => item.JobNumber).IsUnique();
        demo.Property(item => item.Note).HasMaxLength(DemoProject.MaximumNoteLength);

        var project = modelBuilder.Entity<Project>();
        project.ToTable("Projects", table =>
        {
            table.HasCheckConstraint("CK_Projects_JobNumber", "length(JobNumber) > 0 AND JobNumber = trim(JobNumber)");
            table.HasCheckConstraint("CK_Projects_SiteId", "length(trim(SiteId)) > 0");
            table.HasCheckConstraint("CK_Projects_SiteName", "length(trim(SiteName)) > 0");
        });
        project.HasKey(item => item.Id);
        project.Property(item => item.JobNumber).IsRequired().UseCollation("NOCASE");
        project.Property(item => item.SiteId).IsRequired();
        project.Property(item => item.SiteName).IsRequired();
        project.HasIndex(item => item.JobNumber).IsUnique();
        project.HasMany(item => item.WorkItems)
            .WithOne()
            .HasForeignKey(item => item.ProjectId)
            .OnDelete(DeleteBehavior.Restrict);
        project.Navigation(item => item.WorkItems).UsePropertyAccessMode(PropertyAccessMode.Field);

        var workItem = modelBuilder.Entity<WorkItem>();
        workItem.ToTable("WorkItems", table =>
        {
            table.HasCheckConstraint("CK_WorkItems_Type", "Type IN ('Small', 'Civil', 'Tower', 'Other')");
            table.HasCheckConstraint("CK_WorkItems_RequiredCrewCount",
                "typeof(RequiredCrewCount) = 'integer' AND RequiredCrewCount BETWEEN 1 AND 2147483647");
            table.HasCheckConstraint("CK_WorkItems_EstimatedHalfDays",
                "typeof(EstimatedHalfDays) = 'integer' AND EstimatedHalfDays BETWEEN 1 AND 2147483647");
        });
        workItem.HasKey(item => item.Id);
        workItem.Property(item => item.Type).HasConversion<string>();
        workItem.Property(item => item.RequiredCrewCount);
        workItem.Property(item => item.EstimatedHalfDays);
    }
}
