using System.Windows;

namespace Rigarus.Desktop;

public partial class MainWindow : Window
{
    private readonly MainWindowViewModel model;

    internal MainWindow(MainWindowViewModel model)
    {
        InitializeComponent();
        this.model = model;
        DataContext = model;
    }

    private void SaveNote_Click(object sender, RoutedEventArgs e) => model.SaveNote();
}
