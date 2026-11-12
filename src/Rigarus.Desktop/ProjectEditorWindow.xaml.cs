using System.Windows;
using System.Windows.Controls;

namespace Rigarus.Desktop;

public partial class ProjectEditorWindow : Window
{
    private readonly ProjectEditorViewModel model;

    internal ProjectEditorWindow(ProjectEditorViewModel model)
    {
        this.model = model;
        InitializeComponent();
        DataContext = model;
    }

    private void AddWorkItem_Click(object sender, RoutedEventArgs e) => model.AddWorkItem();

    private void RemoveDraft_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button { DataContext: WorkItemInput item })
        {
            model.RemoveDraft(item);
        }
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        if (model.TrySave())
        {
            DialogResult = true;
        }
    }
}
