using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace Rigarus.Desktop;

public partial class ProjectMasterView : UserControl
{
    public ProjectMasterView() => InitializeComponent();

    private ProjectMasterViewModel Model => (ProjectMasterViewModel)DataContext;

    private void OnVisibilityChanged(object sender, DependencyPropertyChangedEventArgs e)
    {
        if (IsVisible && DataContext is ProjectMasterViewModel model)
        {
            model.Open();
        }
    }

    private void Search_Click(object sender, RoutedEventArgs e) => Model.Search();

    private void Search_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter)
        {
            Model.Search();
            e.Handled = true;
        }
    }

    private void NewProject_Click(object sender, RoutedEventArgs e) => OpenEditor(Model.NewProject());

    private void EditProject_Click(object sender, RoutedEventArgs e)
    {
        if (Model.EditProject() is { } editor)
        {
            OpenEditor(editor);
        }
    }

    private void OpenEditor(ProjectEditorViewModel model)
    {
        var dialog = new ProjectEditorWindow(model) { Owner = Window.GetWindow(this) };
        if (dialog.ShowDialog() == true)
        {
            Model.AfterSave(model.SavedId);
        }
    }
}
