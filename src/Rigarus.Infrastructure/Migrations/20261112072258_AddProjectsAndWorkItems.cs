using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Rigarus.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class AddProjectsAndWorkItems : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Projects",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    JobNumber = table.Column<string>(type: "TEXT", nullable: false, collation: "NOCASE"),
                    SiteId = table.Column<string>(type: "TEXT", nullable: false),
                    SiteName = table.Column<string>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Projects", x => x.Id);
                    table.CheckConstraint("CK_Projects_JobNumber", "length(JobNumber) > 0 AND JobNumber = trim(JobNumber)");
                    table.CheckConstraint("CK_Projects_SiteId", "length(trim(SiteId)) > 0");
                    table.CheckConstraint("CK_Projects_SiteName", "length(trim(SiteName)) > 0");
                });

            migrationBuilder.CreateTable(
                name: "WorkItems",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    ProjectId = table.Column<int>(type: "INTEGER", nullable: false),
                    Type = table.Column<string>(type: "TEXT", nullable: false),
                    RequiredCrewCount = table.Column<int>(type: "INTEGER", nullable: false),
                    EstimatedHalfDays = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_WorkItems", x => x.Id);
                    table.CheckConstraint("CK_WorkItems_EstimatedHalfDays", "typeof(EstimatedHalfDays) = 'integer' AND EstimatedHalfDays BETWEEN 1 AND 2147483647");
                    table.CheckConstraint("CK_WorkItems_RequiredCrewCount", "typeof(RequiredCrewCount) = 'integer' AND RequiredCrewCount BETWEEN 1 AND 2147483647");
                    table.CheckConstraint("CK_WorkItems_Type", "Type IN ('Small', 'Civil', 'Tower', 'Other')");
                    table.ForeignKey(
                        name: "FK_WorkItems_Projects_ProjectId",
                        column: x => x.ProjectId,
                        principalTable: "Projects",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Projects_JobNumber",
                table: "Projects",
                column: "JobNumber",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_WorkItems_ProjectId",
                table: "WorkItems",
                column: "ProjectId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "WorkItems");

            migrationBuilder.DropTable(
                name: "Projects");
        }
    }
}
