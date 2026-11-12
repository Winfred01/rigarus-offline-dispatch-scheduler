using System.Windows;
using Rigarus.Application;
using Rigarus.Infrastructure;

namespace Rigarus.Desktop;

public partial class App : System.Windows.Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var smokeRoot = Environment.GetEnvironmentVariable("RIGARUS_SMOKE_DATA_ROOT");
        var paths = string.IsNullOrEmpty(smokeRoot) ? LocalStoragePaths.ForCurrentUser() : new LocalStoragePaths(smokeRoot);
        var store = new SqliteDemoProjectStore(paths);
        var model = new MainWindowViewModel(new DemoWorkspace(store), new LocalDiagnosticLog(paths));
        model.Initialize(store.Initialize);

        MainWindow = new MainWindow(model);
        MainWindow.Show();
    }
}
