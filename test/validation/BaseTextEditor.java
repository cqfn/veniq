package org.jkiss.dbeaver.ui.editors.text;
import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.ResourcesPlugin;
import org.eclipse.core.runtime.CoreException;
import org.eclipse.jface.action.GroupMarker;
import org.eclipse.jface.action.IAction;
import org.eclipse.jface.action.IMenuManager;
import org.eclipse.jface.action.Separator;
import org.eclipse.jface.text.IDocument;
import org.eclipse.jface.text.IUndoManager;
import org.eclipse.jface.text.TextViewer;
import org.eclipse.jface.text.source.SourceViewer;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.ST;
import org.eclipse.swt.custom.StyledText;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.ui.IEditorInput;
import org.eclipse.ui.IEditorPart;
import org.eclipse.ui.IWorkbenchActionConstants;
import org.eclipse.ui.texteditor.AbstractDecoratedTextEditor;
import org.eclipse.ui.texteditor.IDocumentProvider;
import org.eclipse.ui.texteditor.ITextEditorActionConstants;
import org.jkiss.code.Nullable;
import org.jkiss.dbeaver.runtime.DBWorkbench;
import org.jkiss.dbeaver.ui.ICommentsSupport;
import org.jkiss.dbeaver.ui.ISingleControlEditor;
import org.jkiss.dbeaver.ui.UIUtils;
import org.jkiss.dbeaver.ui.dialogs.DialogUtils;
import org.jkiss.dbeaver.ui.editors.*;
import org.jkiss.dbeaver.utils.ContentUtils;
import org.jkiss.dbeaver.utils.GeneralUtils;
import org.jkiss.utils.IOUtils;
import java.io.*;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;
public abstract class BaseTextEditor extends AbstractDecoratedTextEditor implements ISingleControlEditor {
    public static final String TEXT_EDITOR_CONTEXT = "org.eclipse.ui.textEditorScope";
    public static final String GROUP_SQL_PREFERENCES = "sql.preferences";
    public static final String GROUP_SQL_ADDITIONS = "sql.additions";
    public static final String GROUP_SQL_EXTRAS = "sql.extras";
    private List<IActionContributor> actionContributors = new ArrayList<>();
    public void addContextMenuContributor(IActionContributor contributor) {
        actionContributors.add(contributor);
    }
    public static BaseTextEditor getTextEditor(IEditorPart editor)
    {
        if (editor == null) {
            return null;
        }
        if (editor instanceof BaseTextEditor) {
            return (BaseTextEditor) editor;
        }
        return editor.getAdapter(BaseTextEditor.class);
    }
    @Override
    protected void doSetInput(IEditorInput input) throws CoreException {
        if (input != getEditorInput()) {
            IEditorInput editorInput = getEditorInput();
            if (editorInput instanceof IStatefulEditorInput) {
                ((IStatefulEditorInput) editorInput).release();
            }
        }
        super.doSetInput(input);
    }
}