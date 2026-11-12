# Loaded by Test-M0Desktop.ps1 with -IncludeProjects.
function Invoke-ProjectButton($Window, [string]$Id) {
    $button = Get-Control $Window $Id
    $button.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
}

function Set-ProjectField($Window, [string]$Id, [string]$Text) {
    $field = Get-Control $Window $Id
    $field.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Text)
}

function Assert-ProjectText($Window, [string]$Id, [string]$Expected) {
    $element = Get-Control $Window $Id
    Wait-For -Description "$Id to display '$Expected'" -Probe { $element.Current.Name -eq $Expected } | Out-Null
}

function Open-ProjectBacklog($Window) {
    $navigation = Get-Control $Window 'ProjectsNavigation'
    $navigation.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
    Get-Control $Window 'ProjectBacklog' | Out-Null
}

function Get-ProjectEditor($Window, [System.Diagnostics.Process]$Process, [string]$Title) {
    $editorName = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty, $Title)
    $windowType = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Window)
    $processId = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty, $Process.Id)
    $condition = [System.Windows.Automation.AndCondition]::new($editorName, $windowType, $processId)
    Wait-For -Description "$Title window" -Probe {
        if ($Process.HasExited) {
            throw "The app exited while opening the editor with code $($Process.ExitCode)."
        }
        $editor = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst(
            [System.Windows.Automation.TreeScope]::Children, $condition)
        if ($null -eq $editor) {
            $editor = $Window.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condition)
        }
        $editor
    }
}

function Select-WorkItemType($Editor, [int]$Index, [string]$Name) {
    $selectorId = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'DraftWorkItemType')
    $selectors = $Editor.FindAll([System.Windows.Automation.TreeScope]::Descendants, $selectorId)
    $selector = $selectors[$Index]
    $expand = $selector.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
    $expand.Expand()
    $optionName = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::NameProperty, $Name)
    $option = Wait-For -Description "$Name work item type" -Probe {
        $selector.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $optionName)
    }
    $option.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
    if ($expand.Current.ExpandCollapseState -eq [System.Windows.Automation.ExpandCollapseState]::Expanded) {
        $expand.Collapse()
    }
}

function Search-ProjectBacklog($Window, [string]$Term, [string]$ExpectedCount) {
    Set-ProjectField $Window 'ProjectSearch' $Term
    Invoke-ProjectButton $Window 'SearchProjects'
    Assert-ProjectText $Window 'ProjectResults' $ExpectedCount
}

function Test-ProjectMaster($Window, [System.Diagnostics.Process]$Process) {
    Open-ProjectBacklog $Window
    Assert-ProjectText $Window 'EmptyProjects' 'No projects yet. Create a project to start the backlog.'

    Invoke-ProjectButton $Window 'NewProject'
    $editor = Get-ProjectEditor $Window $Process 'New project'
    Invoke-ProjectButton $editor 'SaveProject'
    Assert-ProjectText $editor 'ProjectEditorError' 'Enter a valid Job #.'
    Set-ProjectField $editor 'DraftJobNumber' 'SYN-007'
    Set-ProjectField $editor 'DraftSiteId' 'SITE-007'
    Set-ProjectField $editor 'DraftSiteName' 'Synthetic Ridge'
    Invoke-ProjectButton $editor 'SaveProject'
    Assert-ProjectText $Window 'ProjectResults' '1 project'
    Assert-ProjectText $Window 'DetailJobNumber' 'SYN-007'

    Invoke-ProjectButton $Window 'NewProject'
    $editor = Get-ProjectEditor $Window $Process 'New project'
    Set-ProjectField $editor 'DraftJobNumber' 'syn-007'
    Set-ProjectField $editor 'DraftSiteId' 'SITE-008'
    Set-ProjectField $editor 'DraftSiteName' 'Duplicate Site'
    Invoke-ProjectButton $editor 'SaveProject'
    Assert-ProjectText $editor 'ProjectEditorError' 'A project with this Job # already exists.'
    $editor.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern).Close()
    Assert-ProjectText $Window 'DetailSiteName' 'Synthetic Ridge'

    Search-ProjectBacklog $Window 'no matching site' '0 projects'
    Assert-ProjectText $Window 'EmptyProjects' 'No projects match your search.'
    Search-ProjectBacklog $Window 'site-007' '1 project'
    Invoke-ProjectButton $Window 'EditProject'
    $editor = Get-ProjectEditor $Window $Process 'Edit project'
    Set-ProjectField $editor 'DraftSiteName' 'Synthetic Summit'
    Invoke-ProjectButton $editor 'AddWorkItem'
    Select-WorkItemType $editor 0 'Civil'
    Set-ProjectField $editor 'DraftCrewCount' '2'
    Set-ProjectField $editor 'DraftHalfDays' '0.5'
    Invoke-ProjectButton $editor 'SaveProject'
    Assert-ProjectText $editor 'ProjectEditorError' 'Work item 1 needs a positive whole number for crews and estimated half-days.'
    Set-ProjectField $editor 'DraftHalfDays' '3'
    Invoke-ProjectButton $editor 'AddWorkItem'
    Select-WorkItemType $editor 1 'Tower'
    Invoke-ProjectButton $editor 'SaveProject'
    Assert-ProjectText $Window 'DetailSiteName' 'Synthetic Summit'
}

function Test-ProjectMasterAfterRestart($Window) {
    Open-ProjectBacklog $Window
    Search-ProjectBacklog $Window 'synthetic summit' '1 project'
    Assert-ProjectText $Window 'DetailJobNumber' 'SYN-007'
    Assert-ProjectText $Window 'DetailSiteId' 'SITE-007'
    $typeId = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'DetailWorkItemType')
    $workItemTypes = @($Window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $typeId) |
        ForEach-Object { $_.Current.Name })
    if ($workItemTypes.Count -ne 2 -or 'Civil' -notin $workItemTypes -or 'Tower' -notin $workItemTypes) {
        throw 'The Civil and Tower work items were not restored.'
    }
    Search-ProjectBacklog $Window 'syn-007' '1 project'
    Write-Host 'PASS: Project Master create, validation, duplicate protection, search, edit, and restart persistence.'
}
