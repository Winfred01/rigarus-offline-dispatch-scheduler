using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Rigarus.Infrastructure.Migrations
{
    /// <inheritdoc />
    public partial class InitialDemo : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "DemoProjects",
                columns: table => new
                {
                    Id = table.Column<int>(type: "INTEGER", nullable: false),
                    JobNumber = table.Column<string>(type: "TEXT", nullable: false),
                    SiteName = table.Column<string>(type: "TEXT", nullable: false),
                    Note = table.Column<string>(type: "TEXT", maxLength: 200, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_DemoProjects", x => x.Id);
                    table.CheckConstraint("CK_DemoProjects_NoteLength", "length(Note) <= 200");
                });

            migrationBuilder.CreateIndex(
                name: "IX_DemoProjects_JobNumber",
                table: "DemoProjects",
                column: "JobNumber",
                unique: true);

            migrationBuilder.InsertData(
                table: "DemoProjects",
                columns: new[] { "Id", "JobNumber", "SiteName", "Note" },
                values: new object[] { 1, "DEMO-001", "Example Site", "Synthetic sample for M0." });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "DemoProjects");
        }
    }
}
